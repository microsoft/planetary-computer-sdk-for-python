from datetime import datetime, timezone


from pydantic import BaseModel, Field
from pystac.utils import datetime_to_str


class SASBase(BaseModel):
    """Base model for responses. Include expiry, use RFC339 datetime"""

    expiry: datetime = Field(alias="msft:expiry")

    class Config:
        json_encoders = {datetime: datetime_to_str}
        allow_population_by_field_name = True


class SignedLink(SASBase):
    """Signed SAS URL response"""

    href: str


class SASToken(SASBase):
    """SAS Token response"""

    token: str

    def sign(self, href: str) -> SignedLink:
        """Signs an href with this token"""
        return SignedLink(href=f"{href}?{self.token}", expiry=self.expiry)

    def ttl(self) -> float:
        """Number of seconds the token is still valid for"""
        return (self.expiry - datetime.now(timezone.utc)).total_seconds()
