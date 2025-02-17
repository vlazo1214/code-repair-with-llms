def convert_steps(selected_steps):
    """Converts selected steps into a binary value (bitmask)."""
    all_steps = ["Bug Finding", "Pattern Matching", "Patch Generation", "Patch Validation"]
    return sum(1 << i for i, step in enumerate(all_steps) if step in selected_steps)