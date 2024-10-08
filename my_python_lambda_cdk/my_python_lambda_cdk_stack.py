from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_codebuild as codebuild,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager  # For fetching the GitHub token
)
from constructs import Construct  # CDK v2 uses 'Constructs' instead of 'core'

class MyPythonLambdaCdkStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # S3 bucket for CodePipeline artifacts
        bucket = s3.Bucket(self, "MyPipelineBucket",
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            versioned=True
        )

        # Create secrets for API keys
        groq_api_key = secretsmanager.Secret(self, "GroqApiKey")
        openai_api_key = secretsmanager.Secret(self, "OpenAiApiKey")

        # Lambda function with updated runtime and secrets
        lambda_function = _lambda.Function(
            self, "MyLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "GROQ_API_KEY": groq_api_key.secret_value.unsafe_unwrap(),
                "OPENAI_API_KEY": openai_api_key.secret_value.unsafe_unwrap()
            }
        )

        # Grant Lambda function permission to read secrets
        groq_api_key.grant_read(lambda_function)
        openai_api_key.grant_read(lambda_function)

        # Define a CodePipeline source stage
        source_output = codepipeline.Artifact()

        # Get GitHub token from SecretsManager
        github_token = secretsmanager.Secret.from_secret_name_v2(self, "GitHubToken", "github-t")

        source_action = codepipeline_actions.GitHubSourceAction(
            action_name="GitHub_Source",
            owner="shivam10lm",
            repo="AI-Teaching-Assistant",
            oauth_token=github_token.secret_value,
            output=source_output,
            branch="main"
        )

        # Define a CodeBuild project with updated runtime
        build_project = codebuild.PipelineProject(self, "BuildProject",
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0
            ),
            build_spec=codebuild.BuildSpec.from_source_filename("buildspec.yml")
        )

        # CodePipeline build stage
        build_action = codepipeline_actions.CodeBuildAction(
            action_name="Build",
            project=build_project,
            input=source_output,
            outputs=[codepipeline.Artifact()]
        )

        # CodePipeline deploy stage
        deploy_action = codepipeline_actions.LambdaInvokeAction(
            action_name="Deploy",
            lambda_=lambda_function
        )

        # CodePipeline with encryption
        pipeline = codepipeline.Pipeline(self, "MyPipeline",
            pipeline_name="MyApplicationPipeline",
            stages=[
                codepipeline.StageProps(stage_name="Source", actions=[source_action]),
                codepipeline.StageProps(stage_name="Build", actions=[build_action]),
                codepipeline.StageProps(stage_name="Deploy", actions=[deploy_action])
            ],
            artifact_bucket=bucket,
            cross_account_keys=True
        )

        # Grant permissions to CodePipeline to invoke the Lambda function
        lambda_function.grant_invoke(pipeline.role)
