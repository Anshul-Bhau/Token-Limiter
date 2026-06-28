import random
import string
from locust import HttpUser, task, between

class RateLimiterUser(HttpUser):
    wait_time = between(0, 0.01)

    def on_start(self):
        self.client_key = "loadtest:" + "".join(random.choices(string.ascii_lowercase, k=8))

    @task
    def check_rate(self):
        self.client.post("/check",
                        json={"client_key": self.client_key})