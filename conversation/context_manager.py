def maintain_context(history):
    # If using simple truncation
    return history[-5:]  # Could lose important early context 