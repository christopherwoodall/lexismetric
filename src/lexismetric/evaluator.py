import os
import json
import yaml
import asyncio
import textstat
from openai import AsyncOpenAI
from pathlib import Path
from datetime import datetime


class LexisMetric:
    def __init__(self, config_dir="./config", log_dir="./logs"):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set.")

        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1", api_key=self.api_key
        )

        self.config_path = Path(config_dir)
        self.log_path = Path(log_dir)
        self.log_path.mkdir(parents=True, exist_ok=True)

        self.metrics_list = [
            "flesch_kincaid_grade",
            "smog_index",
            "coleman_liau_index",
            "automated_readability_index",
            "dale_chall_readability_score",
            "difficult_words",
            "linsear_write_formula",
            "gunning_fog",
            "text_standard",
            "fernandez_huerta",
            "szigriszt_pazos",
            "gutierrez_polini",
            "crawford",
            "gulpease_index",
            "osman",
        ]

    def load_config(self, filename):
        file_path = self.config_path / filename
        with open(file_path, "r") as f:
            return yaml.safe_load(f)

    def get_all_readability_metrics(self, text):
        results = {}
        for metric in self.metrics_list:
            try:
                method = getattr(textstat, metric)
                results[metric] = method(text)
            except AttributeError:
                results[metric] = None
        return results

    async def process_prompt(self, label, model_id, prompt, semaphore):
        """Asynchronous worker with concurrency control via semaphore."""
        # Note: Pre-request metrics can run outside the semaphore to save time
        in_metrics = self.get_all_readability_metrics(prompt)

        try:
            # Entry point for concurrent limiting
            async with semaphore:
                response = await self.client.chat.completions.create(
                    model=model_id, messages=[{"role": "user", "content": prompt}]
                )

            output_text = response.choices[0].message.content
            out_metrics = self.get_all_readability_metrics(output_text)

            print(f"Completed: {label} | Prompt: {prompt[:30]}...")

            return {
                "timestamp": datetime.now().isoformat(),
                "model": label,
                "prompt": prompt,
                "metrics_in": in_metrics,
                "metrics_out": out_metrics,
            }
        except Exception as e:
            print(f"Error processing {label} with prompt '{prompt[:20]}': {e}")
            return None

    async def run(self):
        models_cfg = self.load_config("models.yaml")
        prompts_cfg = self.load_config("prompts.yaml")

        # semaphore with a limit of 10
        semaphore = asyncio.Semaphore(10)

        tasks = []
        for model in models_cfg["models"]:
            for prompt in prompts_cfg["prompts"]:
                tasks.append(
                    self.process_prompt(model["label"], model["id"], prompt, semaphore)
                )

        results = await asyncio.gather(*tasks)
        final_results = [r for r in results if r is not None]
        self.save_logs(final_results)

    def save_logs(self, results):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"eval_{timestamp}.json"
        full_path = self.log_path / filename

        with open(full_path, "w") as f:
            json.dump(results, f, indent=4)
        print(f"Logs saved to: {full_path}")
