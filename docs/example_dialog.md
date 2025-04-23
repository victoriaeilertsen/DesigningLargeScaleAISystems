# Sample dialogue: shopper and shopping‑assistant agent

This dialogue shows the target interaction flow.  
Key rules:

1. The user must explicitly pick **one** product before it can be added to the wishlist.  
2. The user sets the price‑alert threshold; the agent simply asks for it.  
3. The agent may suggest **one** clearly superior but more expensive upgrade option (10‑25 % above budget) and offer to track it.

---

## Full conversation

**User:** Hi, I’m looking for wireless headphones.  
**Agent:** Sure! What’s your budget?  

**User:** Up to 400 PLN.  
**Agent:** Got it. Do you prefer a specific brand, or should I focus on best price‑to‑quality?  

**User:** Best price‑to‑quality, please.  
**Agent:** Understood. I’ve found three strong options:

1. **SoundCore Q30** – 379 PLN (active noise cancelling, 40 h battery)  
2. **Sony WH‑CH520** – 349 PLN (50 h battery, no ANC)  
3. **JBL Tune 720BT** – 399 PLN (balanced sound, 70 h battery)  

If you’re open to stretching the budget a little, there’s **Sony WH‑XB910N** at 499 PLN with superior ANC and build quality.  
Which one interests you most?

---

### Branch A – user picks an in‑budget option

**User:** I’ll go with the SoundCore Q30.  
**Agent:** Excellent choice. The current price is 379 PLN.  
What’s the maximum price you’d like to pay before I notify you?

**User:** Track it at 350 PLN.  
**Agent:** Done! I’ve added SoundCore Q30 to your wishlist and will alert you whenever the price drops to 350 PLN or lower.

---

### Branch B – user asks about the upgrade option

**User:** Tell me more about the Sony WH‑XB910N.  
**Agent:** It’s currently 499 PLN – great ANC and premium build.  
Would you like me to alert you if it ever drops to 400 PLN or below?

**User:** Yes, please.  
**Agent:** Sure thing! I’ll track Sony WH‑XB910N and ping you when it hits 400 PLN.

---

## User intents covered

- Product search with constraints (category, budget)  
- Preference clarification (brand vs. best value)  
- Product suggestion list  
- Mandatory single‑item selection  
- Wishlist addition  
- User‑defined price‑tracking threshold  
- Optional upgrade suggestion + alert
