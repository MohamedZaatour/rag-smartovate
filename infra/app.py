#!/usr/bin/env python3
import aws_cdk as cdk

from infra.infra_stack import SmartovateRagStack
from infra.ecs_stack import SmartovateRagEcsStack

app = cdk.App()

SmartovateRagStack(app, "SmartovateRagStack",
    env=cdk.Environment(account="123456789012", region="us-west-2"),
)

SmartovateRagEcsStack(app, "SmartovateRagEcsStack",
    env=cdk.Environment(account="123456789012", region="us-west-2"),
)

app.synth()