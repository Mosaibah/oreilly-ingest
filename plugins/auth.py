import time

from .base import Plugin


class AuthPlugin(Plugin):
    def validate_session(self) -> bool:
        jwt_status = self.http.get_jwt_status()
        if jwt_status is not None:
            return jwt_status["valid"]
        response = self.http.get("/profile/")
        return self._is_valid_profile_response(response)

    def get_status(self) -> dict:
        jwt_status = self.http.get_jwt_status()
        if jwt_status is not None and jwt_status["valid"]:
            return jwt_status
        try:
            response = self.http.get("/api/v1/user/")
            if response.status_code == 200:
                return {"valid": True, "reason": None}
        except Exception:
            pass
        if jwt_status is not None:
            return jwt_status
        response = self.http.get("/profile/")
        return self._parse_profile_response(response)

    def _is_valid_profile_response(self, response) -> bool:
        return (
            "login" not in response.url
            and "signin" not in response.url
            and response.status_code == 200
            and '"user_type":"Expired"' not in response.text
        )

    def _parse_profile_response(self, response) -> dict:
        if "login" in response.url or "signin" in response.url:
            return {"valid": False, "reason": "not_authenticated"}
        if response.status_code != 200:
            return {"valid": False, "reason": "not_authenticated", "status_code": response.status_code}
        if '"user_type":"Expired"' in response.text:
            return {"valid": False, "reason": "subscription_expired"}
        return {"valid": True, "reason": None}
