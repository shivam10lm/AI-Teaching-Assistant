import aws_cdk as core
import aws_cdk.assertions as assertions

from my_python_lambda_cdk.my_python_lambda_cdk_stack import MyPythonLambdaCdkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in my_python_lambda_cdk/my_python_lambda_cdk_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = MyPythonLambdaCdkStack(app, "my-python-lambda-cdk")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
