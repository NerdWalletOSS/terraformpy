"""
Find 48 vCPUs across L, XL, 2XL c4 instances as an ECS cluster

Terraform does not support count for sub-resources, like launch configs on spot fleets.  This will hopefully be added
sometime soon: https://github.com/hashicorp/terraform/issues/7034

In this example the VPC data we pull in from the remote state has 3 AZs/subnets that want to spread our spot fleet our
across.
"""

from terraformpy import Provider, Data, Resource
from pprint import pprint as pp


class VPC(object):
    def __init__(self, name, tiers, **kwargs):
        self.name = name
        self.tiers = tiers
        self.__dict__.update(kwargs)

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)



class Tier(object):
    def __init__(self, name, security_group=None, **kwargs):
        self.name = name
        self.__dict__.update(kwargs)
        self.security_group = security_group

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)

class RDSSecurityGroup(object):
    def __init__(self, name, vpc):
        self.vpc = vpc
        self.name = "{0}-{1}-{2}".format(vpc.region, vpc.name, name)

        self.tf_object = Resource(
            'aws_security_group', self.name,
            name = self.name,
            description = 'rds database open to all hosts in private tiers',
            vpc_id = vpc.vpc_id,
            ingress = [
                dict(
                    from_port=3306,
                    to_port=3306,
                    protocol="tcp",
                    security_groups = [tier.security_group_id for tier in vpc.tiers if tier.access == "private"]
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
                Name="{0}-{1}-rds_all_private".format(vpc.region, vpc.name)
            )
        )

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)

    @property
    def id(self):
        return self.tf_object.id

#hardcoded sg id's and vpc ids for now
app_tier = Tier('application', access='private', security_group_id='sg-b1c92ed5')
db_tier = Tier('database', access='private', security_group_id='sg-89c92eed')
vpc = VPC('stage', vpc_id='vpc-25158340', region='us-east-1',tiers=[app_tier, db_tier])

finpro_sg = RDSSecurityGroup('rds_all_private',vpc)

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
    vpc_security_group_ids = [finpro_sg.id]  
)

pp(finpro_cluster.__dict__)



