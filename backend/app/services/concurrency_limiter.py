import asyncio
import random

class AdaptiveConcurrencyLimiter:
    """
    Controlador de concorrência adaptativo (AIMD: Additive Increase, Multiplicative Decrease)
    com proteção ativa de VRAM (modo local), escalonamento de requisições (staggering)
    e recuo imediato em caso de rate limit (HTTP 429).
    """
    def __init__(self, provider: str = "openrouter", level: str = "Básico"):
        self.provider = (provider or "openrouter").lower()
        self.level = level or "Básico"

        if self.provider in ["local", "ollama"]:
            self.max_limit = 1
            self.min_limit = 1
            self.stagger_delay = 0.0
        elif self.level in ["Teste", "Básico"]:
            self.max_limit = 4
            self.min_limit = 2
            self.stagger_delay = 0.25
        elif self.level == "Intermediário":
            self.max_limit = 5
            self.min_limit = 2
            self.stagger_delay = 0.35
        else:  # Avançado
            self.max_limit = 3
            self.min_limit = 2
            self.stagger_delay = 0.45

        self.current_limit = self.max_limit
        self.active_count = 0
        self.success_streak = 0
        self._cond = asyncio.Condition()

    async def acquire(self):
        async with self._cond:
            while self.active_count >= self.current_limit:
                await self._cond.wait()
            self.active_count += 1
        if self.stagger_delay > 0:
            await asyncio.sleep(self.stagger_delay)

    async def release(self):
        async with self._cond:
            self.active_count = max(0, self.active_count - 1)
            self._cond.notify_all()

    async def on_success(self):
        async with self._cond:
            self.success_streak += 1
            if self.success_streak >= 6 and self.current_limit < self.max_limit:
                self.current_limit = min(self.max_limit, self.current_limit + 1)
                self.success_streak = 0
                print(f"[AdaptiveLimiter] Estável. Concorrência expandida para {self.current_limit} workers.")
                self._cond.notify_all()

    async def on_rate_limit(self, backoff_secs: float = 3.5):
        async with self._cond:
            self.success_streak = 0
            if self.current_limit > self.min_limit:
                old = self.current_limit
                self.current_limit = max(self.min_limit, self.current_limit - 1)
                print(f"[AdaptiveLimiter] Rate limit detectado. Concorrência reduzida de {old} para {self.current_limit} workers.")
        jitter = random.uniform(0.5, 1.5)
        await asyncio.sleep(backoff_secs + jitter)
