# Contributing to ConsensusNet

Thank you for your interest in contributing to ConsensusNet! This document provides guidelines for contributing to the project.

## 🎯 Our Mission

ConsensusNet aims to revolutionize fact-checking through multi-agent AI systems. We welcome contributions that advance this mission while maintaining high code quality and research standards.

## 🚀 Getting Started

1. **Fork the repository**
   ```bash
   git clone https://github.com/hretheum/consensus.net
   cd consensus.net
   ```

2. **Set up your development environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 📝 Contribution Process

1. **Check existing issues** or create a new one describing your proposed change
2. **Follow the coding standards** (see below)
3. **Write tests** for your changes
4. **Update documentation** if needed
5. **Submit a pull request** with a clear description

## 💻 Coding Standards

### Python Code Style
- Follow PEP 8
- Use type hints for all functions
- Maximum line length: 88 characters (Black formatter)
- Docstrings for all public functions and classes

### Example:
```python
from typing import List, Dict

def calculate_consensus(
    agent_votes: List[AgentVote], 
    trust_weights: Dict[str, float]
) -> ConsensusResult:
    """
    Calculate weighted consensus from agent votes.
    
    Args:
        agent_votes: List of votes from different agents
        trust_weights: Trust scores for each agent
        
    Returns:
        ConsensusResult with verdict and confidence
    """
    # Implementation
```

### Git Commit Messages
- Use present tense ("Add feature" not "Added feature")
- Keep first line under 50 characters
- Reference issue numbers when applicable

Example:
```
Add Byzantine fault tolerance to consensus engine (#42)

- Implement PBFT algorithm for agent voting
- Add cryptographic verification of votes
- Include tests for 33% malicious agents
```

## 🧪 Testing

- Write unit tests for all new functions
- Maintain >80% code coverage
- Run tests before submitting PR:
  ```bash
  pytest tests/
  pytest --cov=consensusnet tests/
  ```

## 📚 Documentation

- Update relevant .md files in `docs/`
- Add docstrings to new code
- Include examples for complex features
- Update README.md if adding major features

## 🏗️ Architecture Guidelines

Follow the ECAMAN architecture as described in [docs/architecture/ARCHITECTURE_RECOMMENDATION.md](docs/architecture/ARCHITECTURE_RECOMMENDATION.md):

1. **Maintain separation of concerns** between layers
2. **Use dependency injection** for testability
3. **Follow the agent interface** for new agent types
4. **Document architectural decisions** in `decisions/`

## 🔍 Code Review Process

All contributions go through code review:
1. Automated tests must pass
2. At least one maintainer approval required
3. Address all review comments
4. Squash commits before merging

## 🐛 Reporting Issues

When reporting issues, please include:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- System information (OS, Python version)
- Relevant logs or error messages

## 💡 Feature Requests

We welcome feature requests! Please:
- Check if similar request exists
- Describe the use case clearly
- Explain how it fits ConsensusNet's mission
- Consider implementing it yourself!

## 🏆 Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Considered as co-authors for related research papers

## ❓ Questions?

- Open an issue with the "question" label
- Join our [Discord server](https://discord.gg/consensusnet) (coming soon)
- Email: consensus@example.com (update this)

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for helping make ConsensusNet better! 🎉