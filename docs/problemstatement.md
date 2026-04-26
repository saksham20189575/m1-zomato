# Problem statement: AI-powered restaurant recommendations (Zomato-style)

Build a restaurant recommendation service inspired by Zomato. The system should suggest places to eat by combining **structured restaurant data** with a **large language model (LLM)** so recommendations feel personalized and easy to understand—not just a filtered list.

## Objective

Design and implement an application that:

- Accepts **user preferences** (for example: location, budget, cuisine, minimum rating, and free-text constraints).
- Uses a **real-world restaurant dataset** for grounding.
- Calls an **LLM** to rank options, explain choices, and optionally summarize results.
- Presents **clear, scannable output** so users can act on the recommendations quickly.

## System workflow

### 1. Data ingestion

- Load and preprocess the Zomato-style dataset from Hugging Face: [ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation).
- Retain fields that matter for matching and display—for example: restaurant name, location, cuisine, cost, rating, and any other attributes that improve relevance.

### 2. User input

Collect preferences such as:

- **Location** (e.g. Delhi, Bangalore).
- **Budget** (e.g. low, medium, high).
- **Cuisine** (e.g. Italian, Chinese).
- **Minimum rating**.
- **Additional constraints** (e.g. family-friendly, quick service, outdoor seating)—including natural-language preferences if your design supports them.

### 3. Integration layer

- **Filter** the dataset using structured criteria so the LLM works on a manageable, relevant candidate set.
- **Format** those candidates for the model (tables, JSON, or another consistent structure).
- **Craft prompts** that instruct the LLM to reason over the data, respect hard constraints, and rank or compare options fairly.

### 4. Recommendation engine

Use the LLM to:

- **Rank** restaurants (or produce an ordered shortlist).
- **Explain** why each pick fits the user’s stated preferences.
- **Optionally** provide a brief summary of the overall set of suggestions.

### 5. Output display

Present the top recommendations in a **user-friendly** layout. For each item, surface at least:

- Restaurant name  
- Cuisine  
- Rating  
- Estimated cost  
- **AI-generated explanation** tying the choice back to the user’s input  

---

**Success in one line:** grounded, preference-aware recommendations with transparent reasoning, built on real data and an LLM—not filters alone.
