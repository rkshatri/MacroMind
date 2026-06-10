from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from rag.embedder import load_vector_store
from agent.ppo_agent import step_to_time
import os

def build_query(meal_plan):
    parts = []
    parts.append(f"{meal_plan.get('schedule_type', 'regular')} day meal timing")

    totals = meal_plan.get('totals', {})
    targets = meal_plan.get('targets', {})

    if targets.get('protein', 1) > 0:
        protein_pct = totals.get('protein', 0) / targets.get('protein', 1)
        if protein_pct < 0.8:
            parts.append("protein deficit meal spacing")

    parts.append("hunger management schedule constraints")
    return " ".join(parts)

def format_steps(steps):
        if not steps:
            return None
        sorted_steps = sorted(set(steps))
        times = [step_to_time(step - 1) for step in sorted_steps]
        return ", ".join(times)

def retrieve_context(query, vector_store, k=3):
    results = vector_store.similarity_search(query, k=k)
    context = "\n\n".join([r.page_content for r in results])
    sources = list(set([
        os.path.basename(r.metadata['source']).replace('.txt', '')
        for r in results
    ]))
    return context, sources


def format_meals(meals):
    formatted_lines = []
    for meal in meals:
        time = meal.get("time", "Unknown time")
        food = meal.get("food", "Unknown food")
        calories = meal.get("calories", 0)
        protein = meal.get("protein", 0)
        carbs = meal.get("carbs", 0)
        fat = meal.get("fat", 0)
        formatted_lines.append(
            f"{time} — {food} ({calories} cal, {protein}g protein, {carbs}g carbs, {fat}g fat)"
        )
    return "\n".join(formatted_lines)


def format_macros(macro_dict):
    ordered_keys = ["calories", "protein", "carbs", "fat"]
    formatted = []
    for key in ordered_keys:
        if key in macro_dict:
            value = macro_dict[key]
            suffix = " cal" if key == "calories" else "g"
            formatted.append(f"{key.capitalize()}: {value}{suffix}")

    return ", ".join(formatted)


def explain_meal_plan(meal_plan, vector_store):
    query = build_query(meal_plan)
    context, sources = retrieve_context(query, vector_store)
    meals_formatted = format_meals(meal_plan.get("meals", []))
    totals_formatted = format_macros(meal_plan.get("totals", {}))
    targets_formatted = format_macros(meal_plan.get("targets", {}))

    source_line = (
        "Nutrition knowledge sources: " + ", ".join(sources)
        if sources
        else "Nutrition knowledge sources: none retrieved"
    )

    template = """You are an expert nutrition coach agent explaining your generated daily meal plan to a user in a conversational tone.

NUTRITION KNOWLEDGE:
{context}

{source_line}

YOUR GENERATED MEAL PLAN:
Schedule: {schedule}
Meals eaten:
{meals_formatted}

Daily totals: {totals_formatted}
Daily targets: {targets_formatted}

INSTRUCTIONS:
Analyze the plan and explain every key decision (timing, food selection, and schedule impact). 

CRITICAL STYLE RULES:
- Do not include ANY introductory or concluding meta-text. Do not say "Here is the explanation," "I'd be happy to help," or "Let's look at the plan." Start immediately with the first analytical point.
- Do not make up facts not present in the nutrition knowledge provided above. Cite the sources.
"""

    prompt = PromptTemplate(
        template=template,
        input_variables=[
            "context",
            "source_line",
            "schedule",
            "meals_formatted",
            "totals_formatted",
            "targets_formatted",
        ],
    )

    schedule_type = meal_plan.get("schedule_type", "Unknown")
    busy_times = format_steps(meal_plan.get("busy_steps") or [])
    workout_times = format_steps(meal_plan.get("workout_steps") or [])
    schedule_parts = [f"{schedule_type} day"]
    if busy_times:
        schedule_parts.append(f"busy blocks at {busy_times}")
    if workout_times:
        schedule_parts.append(f"workout sessions at {workout_times}")
    schedule = ", ".join(schedule_parts)

    prompt_text = prompt.format(
        context=context or "No nutrition knowledge available.",
        source_line=source_line,
        schedule=schedule,
        meals_formatted=meals_formatted or "No meals provided.",
        totals_formatted=totals_formatted or "No totals provided.",
        targets_formatted=targets_formatted or "No targets provided.",
    )
    print(prompt_text)

    llm = OllamaLLM(model="llama3.2")
    explanation = llm.invoke(prompt_text)
    return explanation
