#!/usr/bin/env python3
import aws_cdk as cdk

from infra.infra_stack import SmartovateRagStack

app = cdk.App()

SmartovateRagStack(app, "SmartovateRagStack",
    env=cdk.Environment(account="123456789012", region="us-west-2"),
)

app.synth()