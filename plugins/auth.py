from .base import Plugin


class AuthPlugin(Plugin):
    def validate_session(self) -> bool:
        response = self.http.get("/profile/", allow_redirects=False)
        if response.status_code != 200:
            return False
        if '"user_type":"Expired"' in response.text:
            return False
        return True

    def get_status(self) -> dict:
        response = self.http.get("/profile/", allow_redirects=False)

        if response.status_code != 200:
            return {"valid": False, "reason": "not_authenticated"}

        if '"user_type":"Expired"' in response.text:
            return {"valid": False, "reason": "subscription_expired"}

        return {"valid": True, "reason": None}
