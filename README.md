# A2A Supply Chain Agents

An autonomous multi-agent system for supply chain decision-making, built around Google's Agent-to-Agent (A2A) architecture pattern. Two independent AI agents run as separate services, publish agent cards describing their own capabilities, and discover and call each other dynamically rather than being hardcoded together.

This project reimplements the concept from Google's "Build an Autonomous Supply Chain with Gemini & AlloyDB AI" codelab, adapted to run entirely on free, local tools instead of paid Google Cloud infrastructure.


## 🚀 Live Demo

**Watch the complete Agent-to-Agent workflow demonstration on LinkedIn:**  
https://www.linkedin.com/posts/himani-hassija-116b46324_agenticai-multiagentsystems-googlea2a-ugcPost-7480602310876811264-uPri/?utm_source=social_share_send&utm_medium=member_desktop_web&rcm=ACoAAFIJ8SIB9gpcxsPWMGXkc4n7M8ZtZuJpGyI


## Overview

The system solves a simple supply chain problem: given an image of inventory items, identify what is present, then automatically find the best matching supplier for those items.

Two agents accomplish this together.

### Vision Agent

Analyzes an image and reports what it contains. Instead of asking the language model to guess counts or categories from the image directly, the agent instructs the model to write and execute real Python code to verify what it sees. This produces grounded, verifiable answers instead of hallucinated estimates.

### Supplier Agent

Takes a text description of an item and searches a supplier database using vector similarity. Each supplier's description is stored as an embedding, and incoming queries are embedded the same way and ranked using cosine distance, so semantically similar suppliers surface even without exact keyword matches.

### Orchestrator

A lightweight coordinator that:

1. Discovers both agents by requesting their agent cards
2. Sends an image to the Vision Agent and receives a plain language description
3. Passes that description to the Supplier Agent
4. Returns the ranked supplier matches

Each agent is a separate Flask service with its own port and its own `/.well-known/agent.json` agent card. The orchestrator does not hardcode what each agent can do. It reads that information from the agent cards at runtime, which is the core idea behind the A2A pattern.

## Architecture

```
            +------------------+
            |   Orchestrator   |
            +------------------+
                 |         |
     discover /  |         |  discover /
     invoke       |         |   invoke
                 v         v
      +----------------+  +------------------+
      |  Vision Agent  |  |  Supplier Agent   |
      |  (port 5001)   |  |  (port 5002)      |
      +----------------+  +------------------+
              |                     |
         Gemini API           Gemini API
      (code execution)      (embeddings)
                                    |
                              PostgreSQL
                              + pgvector
```

## Tech Stack

* Language model: Google Gemini API (free tier via Google AI Studio)
* Backend: Python, Flask
* Database: PostgreSQL with the pgvector extension
* Similarity search: cosine distance via pgvector's `<=>` operator
* Agent communication: HTTP, following the A2A agent card discovery pattern

## Project Structure

```
run_all.py                  Single entry point. Starts both agents and runs the full pipeline.
vision_agent_server.py       Vision Agent as a standalone Flask service.
supplier_agent_server.py     Supplier Agent as a standalone Flask service.
orchestrator.py              Standalone orchestrator, used when running agents separately.
vision_agent.py               Original standalone Vision Agent script.
find_supplier.py             Standalone similarity search script.
setup_database.py            Creates the suppliers table with a pgvector column.
populate_suppliers.py        Inserts sample suppliers with generated embeddings.
test_connection.py           Basic Gemini API connectivity check.
flowers.png                  Sample test image.
docker-compose.yml            Optional local PostgreSQL and pgvector setup via Docker.
.env.example                  Template for required environment variables.
```

## Setup

### Requirements

* Python 3.11 or later
* A free Gemini API key from Google AI Studio
* A PostgreSQL database with the pgvector extension. Either:
  * A local instance via Docker (`docker-compose.yml` included), or
  * A free hosted instance such as Neon, which supports pgvector out of the box

### Installation

```
pip install flask requests psycopg2-binary python-dotenv google-genai
```

### Environment variables

Copy `.env.example` to `.env` and fill in your own values.

```
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
```

Never commit `.env` to version control. It is already excluded via `.gitignore`.

### Database setup

```
python setup_database.py
python populate_suppliers.py
```

The first script creates the `suppliers` table with a vector column sized for Gemini's embedding output. The second inserts sample suppliers, each with a generated embedding.

### Running the system

```
python run_all.py
```

This starts both agents in the background and runs the full discover, analyze, and match pipeline in one process. Expected output includes the discovered agent cards, the Vision Agent's description of the sample image, and the ranked list of matching suppliers.

## Example Output

```
Found: VisionAgent
Found: SupplierAgent

Vision Agent says: This image shows 7 orange, 9 yellow, and 8 pink flowers.

Top supplier matches:
1. Sunrise Supplies, Orange Blossoms, distance 0.3091
2. Petal and Co., Pink Flowers, distance 0.3312
3. Garden Fresh Traders, Mixed Flower Packs, distance 0.3329
```

## Design Notes

The Vision Agent's use of code execution instead of direct visual estimation is intentional. Language models are known to produce plausible sounding but inaccurate counts when asked to eyeball quantities in an image. Requiring the model to write and run verification code produces answers that are checked rather than guessed.

The A2A pattern was chosen over a simple function call approach because it more closely reflects how autonomous agent systems are expected to scale. In a larger system, agents could be added, removed, or updated independently, as long as they continue to publish a valid agent card. The orchestrator does not need to know about a new agent in advance. It only needs to know where to look.

## Future Work

* Expand the supplier database beyond the current sample set
* Add a persistent A2A discovery registry so agents can be found without hardcoded URLs
* Add a second vision skill, such as damage or defect detection, to demonstrate multi-skill agent cards
* Deploy each agent as an independently hosted service rather than running them in a single process
