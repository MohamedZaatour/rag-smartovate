#!/usr/bin/env python3
import os

import aws_cdk as cdk
from dotenv import load_dotenv
from infra.ecs_stack import SmartovateRagEcsStack
from infra.infra_stack import SmartovateRagStack

# Reglages lus dans infra/.env (ignore par Git), comme COLLECTION_NAME.
load_dotenv()

app = cdk.App()

# ID du compte AWS lu dans infra/.env : il ne figure pas dans le depot public.
env = cdk.Environment(
    account=os.environ["AWS_ACCOUNT_ID"],
    region="us-west-2",
)

SmartovateRagStack(app, "SmartovateRagStack",
    env=env,
)

SmartovateRagEcsStack(app, "SmartovateRagEcsStack",
    env=env,
)

app.synth()