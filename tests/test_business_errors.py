import unittest

from app.business import BusinessService
from app.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessRuleError,
    ResourceNotFoundError,
)


class TestBusinessService(unittest.TestCase):

    def test_authenticated_user_is_accepted(self):
        user = object()

        BusinessService.require_authenticated(user)

    def test_missing_user_raises_authentication_error(self):
        with self.assertRaises(AuthenticationError):
            BusinessService.require_authenticated(None)

    def test_authorized_role_is_accepted(self):
        BusinessService.require_authorized(
            {"Manager", "Staff"},
            "Manager"
        )

    def test_unauthorized_role_raises_error(self):
        with self.assertRaises(AuthorizationError):
            BusinessService.require_authorized(
                {"Manager"},
                "Staff"
            )

    def test_existing_resource_is_accepted(self):
        resource = object()

        result = BusinessService.require_resource(
            resource,
            "Customer"
        )

        self.assertIs(
            result,
            resource
        )

    def test_missing_resource_raises_error(self):
        with self.assertRaises(ResourceNotFoundError):
            BusinessService.require_resource(
                None,
                "Customer"
            )

    def test_valid_business_condition(self):
        BusinessService.require_business_condition(
            True,
            "This should not fail."
        )

    def test_invalid_business_condition(self):
        with self.assertRaises(BusinessRuleError):
            BusinessService.require_business_condition(
                False,
                "The operation is not allowed."
            )


if __name__ == "__main__":
    unittest.main()