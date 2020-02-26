import boto3
import os

def lambda_handler(event, context):
    # boto3 clients
    sts = boto3.client('sts')
    securityhub = boto3.client('securityhub')
    # create env vars
    awsRegion = os.environ['AWS_REGION']
    lambdaFunctionName = os.environ['AWS_LAMBDA_FUNCTION_NAME']
    masterAccountId = sts.get_caller_identity()['Account']
    # parse Security Hub CWE
    securityHubEvent = (event['detail']['findings'])
    for findings in securityHubEvent:
        # parse finding ID
        findingId =str(findings['Id'])
        # parse Account from SecHub Finding
        findingOwner = str(findings['AwsAccountId'])
        for resources in findings['Resources']:
            resourceId = str(resources['Id'])
            # create resource ID
            securityGroupId = resourceId.replace('arn:aws:ec2:' + awsRegion + ':' + findingOwner + ':security-group/', '')
            if findingOwner != masterAccountId:
                memberAcct = sts.assume_role(RoleArn='arn:aws:iam::' + findingOwner + ':role/XA-ElectricEye-Response',RoleSessionName='x_acct_sechub')
                # retrieve creds from member account
                xAcctAccessKey = memberAcct['Credentials']['AccessKeyId']
                xAcctSecretKey = memberAcct['Credentials']['SecretAccessKey']
                xAcctSeshToken = memberAcct['Credentials']['SessionToken']
                # create service client using the assumed role credentials
                ec2 = boto3.resource('ec2',aws_access_key_id=xAcctAccessKey,aws_secret_access_key=xAcctSecretKey,aws_session_token=xAcctSeshToken)
                security_group = ec2.SecurityGroup(securityGroupId)
                try:
                    # remove all rules from security group
                    defaultIngress = security_group.ip_permissions
                    revokeIngress = security_group.revoke_ingress(IpPermissions=defaultIngress)
                    defaultEgress = security_group.ip_permissions_egress
                    revokeEgress = security_group.revoke_egress(IpPermissions=defaultEgress)
                    try:
                        response = securityhub.update_findings(
                            Filters={'Id': [{'Value': findingId,'Comparison': 'EQUALS'}]},
                            Note={'Text': 'All ingress and egress rules were removed from the Security Group and the finding was archived.','UpdatedBy': lambdaFunctionName},
                            RecordState='ARCHIVED'
                        )
                        print(response)
                    except Exception as e:
                        print(e)
                except Exception as e:
                    print(e)
            else:
                try:
                    ec2 = boto3.resource('ec2')
                    security_group = ec2.SecurityGroup(securityGroupId)
                    # remove all rules from security group
                    defaultIngress = security_group.ip_permissions
                    revokeIngress = security_group.revoke_ingress(IpPermissions=defaultIngress)
                    defaultEgress = security_group.ip_permissions_egress
                    revokeEgress = security_group.revoke_egress(IpPermissions=defaultEgress)
                    try:
                        response = securityhub.update_findings(
                            Filters={'Id': [{'Value': findingId,'Comparison': 'EQUALS'}]},
                            Note={'Text': 'All ingress and egress rules were removed from the Security Group and the finding was archived.','UpdatedBy': lambdaFunctionName},
                            RecordState='ARCHIVED'
                        )
                        print(response)
                    except Exception as e:
                        print(e)
                except Exception as e:
                    print(e)