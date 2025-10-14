# Base Tools Template

Common Serena tools for code agents:
- serena:read_file
- serena:create_text_file
- serena:replace_regex
- serena:search_for_pattern

To inherit these, add:
```
tools: inherit-base, <additional-tools>
```

Or explicitly list when you need fewer tools.
