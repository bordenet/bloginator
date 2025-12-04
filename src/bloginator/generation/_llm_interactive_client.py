"""Interactive LLM client that prompts the user for responses."""

from rich.console import Console
from rich.panel import Panel

from bloginator.generation.llm_base import LLMClient, LLMResponse


console = Console()


class InteractiveLLMClient(LLMClient):
    """Interactive LLM client that prompts the user for responses.

    This client displays the prompt to the user and waits for them to provide
    the LLM response. This allows a human (or AI assistant like Claude) to act
    as the LLM for testing and optimization experiments.

    Attributes:
        model: Model name (for display purposes)
        verbose: Whether to print detailed request/response info
    """

    def __init__(
        self,
        model: str = "interactive-llm",
        verbose: bool = False,
        **kwargs: object,
    ) -> None:
        """Initialize interactive LLM client.

        Args:
            model: Model name (for display)
            verbose: Print request/response details
            **kwargs: Ignored (for compatibility)
        """
        self.model = model
        self.verbose = verbose

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """Generate response by prompting the user.

        Args:
            prompt: User prompt/instruction
            temperature: Sampling temperature (displayed to user)
            max_tokens: Maximum tokens (displayed to user)
            system_prompt: System prompt (displayed to user)

        Returns:
            LLMResponse with user-provided content
        """
        # Display the request
        console.print("\n" + "=" * 80, style="bold blue")
        console.print("🤖 INTERACTIVE LLM REQUEST", style="bold blue")
        console.print("=" * 80 + "\n", style="bold blue")

        console.print(f"[bold]Model:[/bold] {self.model}")
        console.print(f"[bold]Temperature:[/bold] {temperature}")
        console.print(f"[bold]Max Tokens:[/bold] {max_tokens}")

        if system_prompt:
            console.print("\n[bold yellow]SYSTEM PROMPT:[/bold yellow]")
            console.print(Panel(system_prompt, border_style="yellow"))

        console.print("\n[bold green]USER PROMPT:[/bold green]")
        console.print(Panel(prompt, border_style="green"))

        # Prompt for response
        console.print("\n" + "=" * 80, style="bold magenta")
        console.print("📝 PLEASE PROVIDE LLM RESPONSE", style="bold magenta")
        console.print("=" * 80, style="bold magenta")
        console.print(
            "[dim]Enter your response below. Type 'END_RESPONSE' on a new line when done:[/dim]\n"
        )

        # Collect multi-line response
        lines = []
        while True:
            try:
                line = input()
                if line.strip() == "END_RESPONSE":
                    break
                lines.append(line)
            except EOFError:
                break

        content = "\n".join(lines)

        # Calculate token counts
        prompt_tokens = len(prompt) // 4
        completion_tokens = len(content) // 4

        if self.verbose:
            console.print("\n[bold cyan]RESPONSE RECEIVED:[/bold cyan]")
            console.print(Panel(content, border_style="cyan"))

        return LLMResponse(
            content=content,
            model=self.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            finish_reason="stop",
        )

    def is_available(self) -> bool:
        """Interactive client is always available.

        Returns:
            Always True
        """
        return True
