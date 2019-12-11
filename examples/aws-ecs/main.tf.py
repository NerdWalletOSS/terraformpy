"""
Find 48 vCPUs across L, XL, 2XL c4 instances as an ECS cluster

Terraform does not support count for sub-resources, like launch configs on spot fleets.  This will hopefully be added
sometime soon: https://github.com/hashicorp/terraform/issues/7034

In this example the VPC data we pull in from the remote state has 3 AZs/subnets that want to spread our spot fleet our
across.
"""

from terraformpy import Data, Provider, Resource, Terraform

# we build our launch configs based on the following data
# each key should be an instance type and the value should be a tuple: (price, vCPUs)
spot_config = {
    "c4.large": (0.105, 2),
    "c4.xlarge": (0.209, 4),
    "c4.2xlarge": (0.419, 8),
}

Terraform(
    backend=dict(
        s3=dict(
            region="us-east-1",
            bucket="terraform-tfstate-bucket",
            key="terraform.tfstate",
            workspace_key_prefix="my_prefix",
            dynamodb_table="terraform_locks",
        )
    )
)

Provider("aws", region="us-west-2", profile="nwdev")

vpc = Data(
    "terraform_remote_state",
    "vpc",
    backend="s3",
    config=dict(
        bucket="nw-terraform",
        key="devops/vpc.tfstate",
        region="us-east-1",
        profile="nwprod",
    ),
)

ami = Data(
    "aws_ami",
    "ecs_ami",
    most_recent=True,
    filter=[
        dict(name="name", values=["*amazon-ecs-optimized"]),
        dict(name="owner-alias", values=["amazon"]),
    ],
)

spot_fleet_role = Resource(
    "aws_iam_role",
    "spot_fleet",
    name="spot_fleet",
    assume_role_policy="""{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "spotfleet.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}""",
)

Resource(
    "aws_iam_policy_attachment",
    "spot_fleet",
    name="spot_fleet",
    roles=[spot_fleet_role.name],
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonEC2SpotFleetRole",
)

ANY_ANY = dict(from_port=0, to_port=0, protocol=-1, cidr_blocks=["0.0.0.0/0"])

sg = Resource(
    "aws_security_group",
    "mycluster",
    name="terraformpy-example-sg",
    description="Example security group for terraformpy",
    vpc_id=vpc.vpc_id,
    ingress=[ANY_ANY],
    egress=[ANY_ANY],
    tags=dict(Name="terraformpy-example-sg",),
)

Resource("aws_ecs_cluster", "mycluster", name="mycluster")

Resource(
    "aws_spot_fleet_request",
    "mycluster_ecs_slaves",
    lifecycle=dict(create_before_destroy=True),
    iam_fleet_role=spot_fleet_role.arn,
    target_capacity=48,  # number of vcpus, since we weight our instances based on that
    spot_price=0.001,  # this will be superceeded by the launch_specification
    valid_until="2099-01-31T17:00:00Z",
    terminate_instances_with_expiration=True,
    allocation_strategy="lowestPrice",  # give it to me cheap!
    launch_specification=[
        dict(
            instance_type=instance_type,
            weighted_capacity=weight,
            spot_price=price / weight,
            ami=ami.id,
            iam_instance_profile="mycluster-role",  # XXX: this should be a resource!
            associate_public_ip_address=False,
            subnet_id="${element(data.terraform_remote_state.vpc.private_subnet_ids, %d)}"
            % count,
            availability_zone="${element(data.terraform_remote_state.vpc.azs, %d)}"
            % count,
            key_name="nw-dev",
            vpc_security_group_ids=[sg.id],
            root_block_device=dict(volume_size="40", volume_type="gp2"),
        )
        for instance_type, (price, weight) in spot_config.items()
        for count in range(3)
    ],
)
