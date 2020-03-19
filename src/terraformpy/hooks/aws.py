from terraformpy.objects import Resource

SECURITY_GROUP_RULE_OPTIONAL_ATTRS = (
    "cidr_blocks",
    "ipv6_cidr_blocks",
    "prefix_list_ids",
    "security_groups",
    "self",
    "description",
)


def fill_in_optional_aws_security_group_rules_attrs(object_id, attrs):
    """Given a set of attrs for an aws_security_group this will ensure any ingress or egress blocks have all of the
    mandatory attributes defined
    """
    attrs = attrs.copy()
    for direction in ("ingress", "egress"):
        if direction not in attrs:
            continue

        for rule in attrs[direction]:
            for optional_attr in SECURITY_GROUP_RULE_OPTIONAL_ATTRS:
                if optional_attr in rule:
                    continue

                rule[optional_attr] = None

    return attrs


def install_aws_security_group_attributes_as_blocks_hook():
    """Installs a hook that ensures that all ingress and egress blocks have all of the mandatory attributes defined
    as None, so that they compile out as null

    See: https://github.com/terraform-providers/terraform-provider-aws/issues/8786#issuecomment-496935442
    """
    Resource.add_hook(
        "aws_security_group", fill_in_optional_aws_security_group_rules_attrs
    )
