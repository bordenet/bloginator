# Debugging Efficiency

> **When to load:** When going in circles or stuck

## Signs You're Going in Circles

- Running the same command 3+ times expecting different results
- Waiting for output that never comes
- Terminal capture returning empty strings repeatedly

## When This Happens

1. **STOP immediately** - Don't run the same thing again
2. **Diagnose root cause** - Check file existence, process status, error logs
3. **Use file redirection** - `command > /tmp/out.txt 2>&1` then `view /tmp/out.txt`
4. **Ask for help** - Generate a Perplexity prompt if truly stuck

## ⛔ WHEN STUCK, ASK FOR PERPLEXITY HELP

**The moment you get blocked, STOP immediately.**

Do NOT continue trying random approaches. Instead:
1. **Generate a detailed Perplexity.ai prompt** for the user
2. Include: what you've tried, why it failed, technical details, environment
3. **Wait for user to return with Perplexity's response**
4. Fresh external research often unblocks problems

This is essential because:
- Training data may be outdated or incomplete
- Perplexity has access to current documentation
- Prevents wasted time on dead-end approaches

