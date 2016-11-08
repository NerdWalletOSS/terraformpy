"""
Find 48 vCPUs across L, XL, 2XL c4 instances as an ECS cluster

Terraform does not support count for sub-resources, like launch configs on spot fleets.  This will hopefully be added
sometime soon: https://github.com/hashicorp/terraform/issues/7034

In this example the VPC data we pull in from the remote state has 3 AZs/subnets that want to spread our spot fleet our
across.
"""

from terraformpy import Provider, Data, Resource


Provider(
    'aws',
    region='us-west-2',
    profile='nwdev'
)


class DataMock(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class VPCData(DataMock):
    """vpc data"""

class TierData(DataMock):
    """describes a tier"""

tier_1 = TierData(
        name = 'private-tier-1',
        access = 'private',
        subnet_ids = ["taco","burrito","nacho"],
        security_group = "sg-89c92eed"
    )

tier_2 = TierData(
        name = 'private-tier-2',
        access = 'private',
        subnet_ids = ["subnet-ea5ca1c1","subnet-f85cec8f","subnet-f3ce1caa"],
        security_group = 'sg-b1c92ed5'
    )

vpc = VPCData(
        vpc_id = 'vpc-25158340',
        #tiers = [tier_1, tier_2],
        tiers = {
            tier_1.name: tier_1,
            tier_2.name: tier_2
        }
    )


sg = Resource(
    'aws_security_group', 'rds_nonsecure',
    name = 'nwstage-rds-nonsecure-sg',
    description = 'Open to all hosts in private tiers',
    vpc_id = vpc.vpc_id,
    ingress = [
        dict(
            from_port=3306,
            to_port=3306,
            protocol="tcp",
            security_groups = [tier.security_group for _,tier in vpc.tiers.items() if tier.access == "private"]
        )
    ],
    egress = [
        dict(
            from_port = 0,
            to_port = 0,
            protocol = "-1",
            cidr_blocks = ["0.0.0.0/0"]
        )

    ],
    tags=dict(
        Name='nwstage-rds-nonsecure-sg'
    )
)

nwstage_private = Resource(
    "aws_db_subnet_group","nwstage",
    name = "nwstage-private",
    description = "Databases in the nwstage private tier",
    subnet_ids = vpc.tiers['private-tier-2'].subnet_ids,
    tags  = dict(
        Name = "nwstage-private",
        cluster = "stage",
        pod = "devops",
        wyatt = "true"
    )
)

params = Resource (
    'aws_rds_cluster_parameter_group','finpro',
    name = "nwstage-finpro",
    description = "Parameters for the nwstage finpro RDS",
    family = "aurora5.6"
)


finpro_cluster = Resource(
    'aws_rds_cluster', 'nwstage-finpro',
    cluster_identifier = "nwstage-finpro",
    availability_zones = ["us-east-1a", "us-east-1c", "us-east-td"],
    master_username = "root",
    master_password = "password",
    final_snapshot_identifier = "nwstage-finpro-final-snapshot",
    backup_retention_period = 7,
    preferred_backup_window = "13:30-14:00",
    preferred_maintenance_window = "wed:15:00-wed:15:30",
    db_subnet_group_name = "nwstage-private",
    db_cluster_parameter_group_name = params.name,
    vpc_security_group_ids = [sg.id]  
)

Resource(
    'aws_rds_cluster_instance','nwstage-finpro',
    cluster_identifier = finpro_cluster.id,
    identifier = 'nwstage-finpro-${count.index}',
    instance_class = "db.r3.large",
    db_subnet_group_name = "nwstage-private",
    count = 2
)
