"""
Pile ECS Fargate - deploiement du conteneur rag-smartovate derriere un ALB (US 4.2).
"""
import os
from pathlib import Path

from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_ec2 as ec2,
    aws_ecr_assets as ecr_assets,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_elasticloadbalancingv2 as elbv2,
    aws_iam as iam,
    aws_logs as logs,
)
from constructs import Construct
from dotenv import dotenv_values, load_dotenv

# Charge infra/.env (ALLOWED_IPS, ...)
load_dotenv()

# --- Bloc 1 : configuration ---
# 02-Developpement/ : contexte de build de l'image (Dockerfile) et fichier .env.docker
RACINE_PROJET = Path(__file__).resolve().parents[2]
FICHIER_ENV_CONTENEUR = RACINE_PROJET / ".env.docker"

# IP autorisees a ouvrir l'application (format x.x.x.x/32, separees par des virgules)
ALLOWED_IPS = [ip.strip() for ip in os.environ["ALLOWED_IPS"].split(",") if ip.strip()]

# Nom FIXE du task role -> ARN connu a l'avance (data access policy OpenSearch)
TASK_ROLE_NAME = "smartovate-rag-task-role"

# Modele d'embedding : MEME valeur que src/ingestion/embeddings.py (a garder synchronise)
MODELE_EMBEDDING = "amazon.titan-embed-text-v2:0"


def lire_variables_conteneur() -> dict:
    """Lit .env.docker : memes variables que le test Docker local (sans secret)."""
    if not FICHIER_ENV_CONTENEUR.exists():
        raise FileNotFoundError(f"Fichier introuvable : {FICHIER_ENV_CONTENEUR}")
    variables = {
        cle: valeur
        for cle, valeur in dotenv_values(FICHIER_ENV_CONTENEUR).items()
        if valeur is not None
    }
    # Garde-fou : avec AWS_PROFILE, boto3 ignorerait le task role (ProfileNotFound)
    if "AWS_PROFILE" in variables:
        raise ValueError(".env.docker ne doit PAS contenir AWS_PROFILE (le task role fournit les identifiants).")
    return variables


class SmartovateRagEcsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # --- Bloc 2 : reseau (VPC dedie, 2 zones, sous-reseaux publics, 0 NAT) ---
        vpc = ec2.Vpc(
            self, "RagVpc",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
            ],
        )

        # --- Bloc 3 : cluster ECS (regroupement logique, gratuit avec Fargate) ---
        cluster = ecs.Cluster(
            self, "RagCluster",
            cluster_name="smartovate-rag-cluster",
            vpc=vpc,
        )

        # --- Bloc 4 : task role (identite de l'application dans AWS) ---
        variables = lire_variables_conteneur()
        region_llm = variables.get("BEDROCK_LLM_REGION") or self.region
        modele_llm = variables["BEDROCK_LLM_MODEL_ID"]      # us.anthropic.claude-haiku-4-5-...
        modele_base = modele_llm.split(".", 1)[1]            # anthropic.claude-haiku-4-5-...
        collection_id = variables["OPENSEARCH_ENDPOINT"].split("//")[-1].split(".")[0]

        task_role = iam.Role(
            self, "RagTaskRole",
            role_name=TASK_ROLE_NAME,
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            description="Application RAG : appels Bedrock et OpenSearch Serverless",
        )

        # Bedrock : Titan (embeddings) + Claude via le profil d'inference "us."
        # et les modeles vers lesquels ce profil route les appels
        task_role.add_to_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeModel"],
            resources=[
                f"arn:aws:bedrock:{self.region}::foundation-model/{MODELE_EMBEDDING}",
                f"arn:aws:bedrock:{region_llm}:{self.account}:inference-profile/{modele_llm}",
                f"arn:aws:bedrock:*::foundation-model/{modele_base}",
            ],
        ))

        # OpenSearch Serverless : porte n.1 (IAM). La porte n.2 = data access policy.
        task_role.add_to_policy(iam.PolicyStatement(
            actions=["aoss:APIAccessAll"],
            resources=[f"arn:aws:aoss:{self.region}:{self.account}:collection/{collection_id}"],
        ))

        # --- Bloc 5 : porte d'entree (ALB) et son vigile (groupe de securite) ---
        sg_alb = ec2.SecurityGroup(
            self, "AlbSecurityGroup",
            vpc=vpc,
            description="ALB RAG : HTTP 80 depuis les IP autorisees uniquement",
        )
        for ip in ALLOWED_IPS:
            sg_alb.add_ingress_rule(ec2.Peer.ipv4(ip), ec2.Port.tcp(80), f"HTTP depuis {ip}")

        alb = elbv2.ApplicationLoadBalancer(
            self, "RagAlb",
            vpc=vpc,
            internet_facing=True,
            security_group=sg_alb,
            idle_timeout=Duration.minutes(5),
        )

        # --- Bloc 6 : service Fargate derriere l'ALB (construct L3 "tout-en-un") ---
        service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "RagService",
            cluster=cluster,
            service_name="smartovate-rag-service",
            load_balancer=alb,
            open_listener=False,          # pas d'ouverture 0.0.0.0/0 : l'acces est gere par sg_alb
            listener_port=80,
            cpu=512,                      # 0,5 vCPU
            memory_limit_mib=1024,        # 1 Go (mesure locale : ~124 Mo au repos)
            desired_count=1,
            min_healthy_percent=100,      # deploiement sans coupure : la nouvelle tache demarre
            max_healthy_percent=200,      # avant l'arret de l'ancienne
            assign_public_ip=True,        # sortie Internet sans NAT (ECR, Bedrock, OpenSearch)
            task_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            health_check_grace_period=Duration.seconds(60),
            circuit_breaker=ecs.DeploymentCircuitBreaker(rollback=True),
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_asset(
                    str(RACINE_PROJET),
                    platform=ecr_assets.Platform.LINUX_AMD64,
                ),
                container_name="rag",
                container_port=8501,
                environment=variables,
                task_role=task_role,
                log_driver=ecs.LogDrivers.aws_logs(
                    stream_prefix="rag",
                    log_retention=logs.RetentionDays.ONE_WEEK,
                ),
            ),
        )

        # --- Bloc 7 : controle de sante et delais ---
        service.target_group.configure_health_check(
            path="/_stcore/health",
            healthy_http_codes="200",
            interval=Duration.seconds(30),
            timeout=Duration.seconds(5),
            healthy_threshold_count=2,
            unhealthy_threshold_count=3,
        )
        # Lors d'un redeploiement : 30 s pour vider l'ancienne tache (au lieu de 300 s)
        service.target_group.set_attribute("deregistration_delay.timeout_seconds", "30")

        # --- Bloc 8 : sortie - ARN du task role (a autoriser dans OpenSearch) ---
        CfnOutput(
            self, "TaskRoleArn",
            value=task_role.role_arn,
            description="ARN a ajouter a la data access policy OpenSearch",
        )
