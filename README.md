# Jamnesia - Poker Hand Management System

A web application to record poker hands using PokerKit, save them in PHH (Poker Hand History) format, and replay them with an interactive visual interface. Built with Flask + HTMX for a lightweight, modern web experience.

## 🎬 Hand Replay Demo

Experience poker hands step-by-step with:
- **Visual poker table** with players positioned around the table
- **Interactive controls** (play, pause, step forward/back, speed control)
- **Real-time state tracking** (pot sizes, stack changes, board progression)
- **Action descriptions** for each move
- **Responsive design** that works on desktop and mobile

Try it: Create a sample hand and click the "🎬 Replay" button!

## Features

- **Hand Input**: Web form interface for entering poker hands with players, stacks, hole cards, board cards, and actions
- **Hand Replay**: Step-by-step visual replay of poker hands with interactive controls
- **PHH Generation**: Generates standard PHH (Poker Hand History) format files
- **Database Storage**: Normalized SQLite schema for efficient storage and retrieval
- **Sample Data**: Quick sample hand creation for testing and demonstration
- **Responsive UI**: Clean interface built with Tailwind CSS and HTMX
- **RESTful API**: JSON endpoints for integration with other tools

## Tech Stack

- **Backend**: Python 3.11+, Flask, SQLAlchemy
- **Frontend**: HTMX, Tailwind CSS
- **PHH Generation**: Custom implementation following PHH specification
- **Database**: SQLite (production-ready for PostgreSQL)
- **Deployment**: Docker-ready for Render or similar platforms

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd jamnesia
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open in browser**
   ```
   http://localhost:8000
   ```

## Usage

### Input a Poker Hand

1. Navigate to "Input Hand" from the main page
2. Configure game settings (small blind, big blind)
3. Add players with their names, stacks, and hole cards
4. Set board cards (flop, turn, river) if applicable
5. Add actions in sequence (fold, check, call, bet, raise) with pot size and remaining stack after each action
6. Click "Save Hand" to generate PHH and store in database

### View Saved Hands

- The main page displays all saved hands
- Click "Details" to view complete hand information
- Click "🎬 Replay" to experience the hand step-by-step
- PHH format is generated automatically and displayed

### Hand Replay Experience

- **Interactive Controls**: Play, pause, step forward/backward, jump to first/last
- **Visual Table**: See players positioned around a poker table
- **Real-time Updates**: Watch pot sizes, stack changes, and board card progression
- **Action Descriptions**: Clear descriptions of each action as it happens
- **Speed Control**: Adjust replay speed from slow (2s) to fast (0.5s)
- **State Tracking**: Accurate tracking of player stacks, bets, and pot throughout the hand

### Create Sample Hand

- Click "Create Sample Hand" on the main page for a quick demo
- This creates a pre-configured hand with Alice, Bob, and Charlie
- Perfect for testing the replay functionality

## API Endpoints

### Save Hand
```http
POST /api/save-hand
Content-Type: application/json

{
  "players": [
    {"name": "Alice", "stack": 100.0},
    {"name": "Bob", "stack": 100.0}
  ],
  "actions": [
    {"player_name": "Alice", "action_type": "bet", "amount": 5.0, "pot_size": 7.0, "remaining_stack": 95.0},
    {"player_name": "Bob", "action_type": "call", "pot_size": 12.0, "remaining_stack": 95.0}
  ],
  "small_blind": 1.0,
  "big_blind": 2.0,
  "hole_cards": {
    "Alice": "AsKh",
    "Bob": "QdQc"
  },
  "flop": "AhKd5c"
}
```

### List Hands
```http
GET /api/hands
```

### Get Hand Details
```http
GET /api/hands/{play_id}
```

### Get Hand Replay Data
```http
GET /api/hands/{play_id}/replay
```
Returns structured replay data with step-by-step game states, including:
- Player positions and stacks at each step
- Pot size progression
- Board card reveals
- Action descriptions and metadata

### Get Hand Replay UI
```http
GET /api/hands/{play_id}/replay-ui
```
Returns HTML interface for hand replay with interactive controls.

### Create Sample Hand
```http
POST /api/create-sample
```

## Database Schema

### hands
- `id`: Primary key
- `play_id`: Unique identifier for the hand
- `game_type`: Type of poker game (default: "No Limit Texas Holdem")
- `board`: Board cards string
- `small_blind`, `big_blind`: Blind amounts
- `phh_content`: Generated PHH format content
- `created_at`: Timestamp

### players
- `id`: Primary key
- `hand_id`: Foreign key to hands table
- `name`: Player name
- `stack`: Starting stack size
- `hole_cards`: Player's hole cards (e.g., "AsKh")
- `position`: Seat position ("SB", "BB", "UTG", "BTN", etc.)

### actions
- `id`: Primary key
- `hand_id`: Foreign key to hands table
- `street`: Betting round ("preflop", "flop", "turn", "river")
- `player_name`: Player who made the action
- `action_type`: Type of action ("fold", "check", "call", "bet", "raise")
- `amount`: Bet/raise amount
- `pot_size`: Pot size after this action
- `remaining_stack`: Player's remaining stack after this action
- `action_order`: Sequence order of the action

## Development

### Project Structure
```
jamnesia/
├── app.py              # Main Flask application
├── models.py           # Database models
├── poker_engine.py     # PokerKit integration
├── requirements.txt    # Python dependencies
├── templates/          # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── input.html
│   ├── hands_list.html
│   ├── hand_detail.html
│   └── hand_replay.html
└── venv/              # Virtual environment
```

### Development Workflow

The project includes comprehensive tooling for development:

```bash
# Quick start with Makefile
make help          # Show all available commands
make dev-install   # Install all dependencies
make test          # Run all tests
make coverage      # Run tests with coverage
make lint          # Check code quality
make format        # Auto-format code
make run           # Start development server

# Or run commands directly:
python run_tests.py                    # Run all tests
python -m unittest test_poker_engine.py # Run specific tests
coverage run run_tests.py && coverage html # Generate coverage report
```

**Test Coverage (90 tests total):**
- **Poker Engine Tests (19 tests)**: PHH generation, hand building, edge cases
- **Database Models Tests (14 tests)**: Model creation, relationships, constraints, replay fields
- **Flask Application Tests (25 tests)**: API endpoints, workflows, error handling, HTML templates
- **Position Enum Tests (15 tests)**: Position handling, validation, display names
- **Position Template Tests (4 tests)**: Template rendering, position display
- **Hand Replay Tests (13 tests)**: Replay API, state progression, UI rendering, integration

All tests use isolated temporary databases and pass 100% of the time.

### Database Migration
The application automatically creates tables on first run. For production deployments with PostgreSQL:

1. Update `DATABASE_URL` environment variable
2. Install PostgreSQL adapter: `pip install psycopg2-binary`

## Deployment

### Environment Variables
- `DATABASE_URL`: Database connection string (default: SQLite)
- `SECRET_KEY`: Flask secret key for sessions

### Docker
```dockerfile
# Basic Dockerfile structure
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [PokerKit](https://pypi.org/project/pokerkit/) - Poker game engine
- [PHH Specification](https://phh.readthedocs.io/en/stable/) - Poker Hand History format
- [HTMX](https://htmx.org/) - Dynamic web interactions
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS framework