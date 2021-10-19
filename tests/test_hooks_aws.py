from terraformpy.hooks.aws import fill_in_optional_aws_security_group_rules_attrs


def test_fill_in_optional_aws_security_group_rules_attrs():
    attrs = {
        "ingress": [
            {"from_port": 0, "to_port": 0, "protocol": -1},
        ],
        "egress": [
            {"from_port": 0, "to_port": 0, "protocol": -1},
        ],
    }

    new_attrs = fill_in_optional_aws_security_group_rules_attrs("foo", attrs)
    assert new_attrs == {
        "ingress": [
            {
                "from_port": 0,
                "to_port": 0,
                "protocol": -1,
                "cidr_blocks": None,
                "ipv6_cidr_blocks": None,
                "prefix_list_ids": None,
                "security_groups": None,
                "self": None,
                "description": None,
            },
        ],
        "egress": [
            {
                "from_port": 0,
                "to_port": 0,
                "protocol": -1,
                "cidr_blocks": None,
                "ipv6_cidr_blocks": None,
                "prefix_list_ids": None,
                "security_groups": None,
                "self": None,
                "description": None,
            },
        ],
    }
