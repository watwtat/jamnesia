# Requirement Spec v1.1: Poker Hand Input / Storage / Replay Web App

## 1. Project Overview

This project enables poker players to enter hand histories via a web form and save them in standard PHH format.  
It also supports saving the data to SQLite or PostgreSQL and includes a replay feature to step through historical hands.

## 2. System Architecture

- **Architecture**: Flask + HTMX  
- **Language**: Python 3.11+  
- **Libraries**: Flask, PokerKit, SQLAlchemy  
- **DB**: SQLite (initial) / PostgreSQL (expandable)  
- **Deployment**: Render (Docker-based)

## 3. Functional Requirements

### 3.1 Poker Hand Input

- Web form input for player names, stacks, board
- Use PokerKit to generate `.phh` files

### 3.2 Database Storage

- Save to SQLite/PostgreSQL
- Use normalized schema

### 3.3 Hand Replay

- Replay hands by PlayID
- Step through each action (Next/Prev)
- Use GameStatus to detect end of hand

## 4. Non-Functional Requirements

- Compatible with modern browsers (Chrome, etc.)
- Use Docker to match local and production environments
- Lightweight UI with HTMX
- Data structure designed for scalability

## 5. Data Model (Simplified)

- `hands(id, game_type, board, created_at)`
- `players(id, hand_id, name, stack, hole_cards)`
- `actions(id, hand_id, street, player_name, action_type, amount, action_order)`

## 6. Use Cases

- **UC-1**: Input hand and generate `.phh`
- **UC-2**: Save to DB
- **UC-3**: Replay by PlayID
- **UC-4**: Step-by-step action replay

## 7. Development Schedule

- **P1**: Input form + `.phh` generation  
- **P2**: SQLite integration  
- **P3**: PostgreSQL support  
- **P4**: Replay UI  
- **P5**: UI polish + deployment

## 8. Future Enhancements

- Graphical stats (VPIP, etc.)
- JSON API output
- Discord integration
- Bulk import of sample hands

## 9. References

- [PokerKit](https://pypi.org/project/pokerkit/)
- [PHH Spec](https://phh.readthedocs.io/en/stable/)
- [HTMX](https://htmx.org/)
- [Render](https://render.com/)
