# Planning Document: Results Chatbot

## 1. Feature Title
Results Chatbot

## 2. Feature Description
Introduces an interactive AI assistant (chatbot) that allows users to conversationally query, modify, and expand a generated futurecast (initial seed prompt, effect tree, and results summary). This feature aims to make the exploration and refinement of futurecasts more dynamic and intuitive. After an initial prediction tree and summary are generated, users can engage with a chatbot that has full contextual awareness of the scenario. Key capabilities would include:
*   **Conversational Q&A:** Users can ask open-ended, natural language questions about the generated futurecast, such as "What are the primary economic impacts predicted in this scenario?", "Can you explain the link between effect A and its child effect B?", or "What underlying assumptions seem to be driving the predictions in the 'Technology Adoption' branch?". The chatbot would synthesize information from the initial prompt, the effect tree, and the summary to provide answers.
*   **Interactive Tree Modification via Chat:** Users could instruct the chatbot to alter the futurecast. For example:
    *   "Change the effect 'Increased remote work adoption' to 'Hybrid work models become dominant'." The chatbot would update the specified effect's content and then re-trigger the prediction engine to regenerate all downstream effects from this modified node, maintaining consistency.
    *   "Remove the entire branch starting with the effect 'Significant decline in commercial real estate'."
*   **Targeted Expansion via Chat:** Users could direct the chatbot to deepen specific parts of the prediction tree: "Expand the leaf effect 'Development of new AI-powered diagnostic tools' by 2 more levels, focusing on implications for rural healthcare." The chatbot would then generate new child effects for the specified node and integrate them seamlessly into the existing tree structure.
This feature centralizes interaction, allowing for a fluid, iterative process of exploring, refining, and extending the futurecast without needing to manually restart or navigate complex editing UIs for every change. It requires sophisticated state management, and careful LLM prompting for modification and expansion tasks.

## 3. Goals & Objectives
*   **Goal:** Enhance user interaction with generated futurecasts by providing a conversational interface for exploration and modification.
*   **Objectives:**
    *   Allow users to ask natural language questions about the futurecast and receive contextually relevant answers.
    *   Enable users to modify existing effects in the futurecast tree through chat commands.
    *   Permit users to remove effects or entire branches from the futurecast tree via chat.
    *   Allow users to expand specific leaf nodes in the futurecast tree by requesting further predictions through chat.
    *   Streamline the process of refining and iterating on futurecasts.
    *   Maintain consistency of the futurecast by re-triggering the prediction engine for relevant downstream effects after modifications.

## 4. Scope

### In Scope (MVP)
*   **Conversational Q&A:**
    *   Ability to ask questions about the current futurecast (initial prompt, effect tree, summary).
    *   Chatbot synthesizes answers based on the available futurecast data.
*   **Basic Interactive Tree Modification via Chat:**
    *   Modify the text content of an existing effect.
    *   Re-trigger prediction engine for downstream effects of the modified node.
*   **Basic Targeted Expansion via Chat:**
    *   Expand a specified leaf effect by a user-defined number of levels.
    *   Integrate newly generated child effects into the existing tree.
*   **Basic Chat UI:** A simple, functional chat interface integrated into the application.
*   **Contextual Awareness:** Chatbot maintains awareness of the current futurecast state.
*   **State Management:** Robust state management for the futurecast data and chat history.

### Out of Scope (Future Enhancements)
*   **Advanced Tree Modification:**
    *   Complex structural changes beyond simple text edits or single branch removal (e.g., merging branches, re-parenting nodes via chat).
    *   Ability to "undo" chat-driven modifications.
*   **Proactive Chatbot Suggestions:** Chatbot suggesting potential areas for expansion or refinement.
*   **Multi-modal Input/Output:** Support for voice commands or visual outputs beyond text.
*   **Saving/Loading Chat Sessions:** Persisting chat history and interactions.
*   **Advanced NLU Capabilities:** Handling highly ambiguous or complex multi-intent user utterances.
*   **User Authentication & Personalization:** Tailoring chatbot behavior or suggestions based on user profiles.
*   **Direct comparison of different futurecast versions generated via chat.**
*   **Full branch removal via chat.** (Re-evaluating complexity for MVP, initially listed in description but potentially complex for a first version).

## 5. High-Level Technical Approach & Architecture

*   **Key Components:**
    *   **Chat UI:** Frontend component for user interaction (e.g., Streamlit input/output, custom web component).
    *   **NLU/Intent Recognition Layer:** Processes user's natural language input to identify intents (e.g., "ask_question", "modify_effect", "expand_effect") and extract relevant entities (e.g., effect ID, new text, expansion depth). This might involve rule-based parsing or a lightweight ML model.
    *   **State Manager:** Manages the current state of the futurecast (effect tree, initial prompt, summary) and the chat history. Ensures data consistency.
    *   **Action Dispatcher:** Based on the recognized intent, triggers appropriate actions (e.g., querying data, calling the LLM for modification, invoking the Prediction Engine).
    *   **LLM Interaction Layer:** Formulates prompts for the primary application LLM to handle Q&A, rephrase modification requests, or generate text for new effects based on user instructions.
    *   **Prediction Engine Interface:** Module to interact with the existing `PredictionEngine` to regenerate or expand parts of the effect tree.
*   **Data Flow (Simplified):**
    1.  User types a message in the Chat UI.
    2.  Message is sent to the NLU/Intent Recognition Layer.
    3.  Intent and entities are extracted.
    4.  Action Dispatcher receives the intent and entities.
    5.  Based on the action:
        *   For Q&A: LLM Interaction Layer queries the State Manager for context and generates an answer.
        *   For Modification/Expansion: LLM Interaction Layer may refine the user's instruction into a structured command. The Action Dispatcher then updates the State Manager and/or calls the Prediction Engine Interface.
    6.  Prediction Engine updates the effect tree if necessary.
    7.  State Manager updates the futurecast.
    8.  Response is sent back to the Chat UI.
*   **Note:** Retrieval Augmented Generation (RAG) is not planned for the initial version due to the large context window of the selected LLM. The chatbot will use the same LLM as the main FutureCast application.

## 6. Key Challenges & Risks
*   **NLU Accuracy:** Reliably interpreting diverse user phrasings for modifications and expansions.
*   **State Management Complexity:** Ensuring the futurecast state remains consistent and accurately reflects chat-driven changes, especially with asynchronous updates from the prediction engine.
*   **LLM Prompt Engineering:** Crafting effective prompts for the LLM to understand modification/expansion instructions and generate desired outputs without unintended side effects.
*   **Maintaining Tree Integrity:** Ensuring that operations like modification and expansion correctly update the tree structure and trigger downstream predictions accurately.
*   **User Experience:** Designing an intuitive chat flow that clearly communicates actions taken by the chatbot and handles errors gracefully.
*   **Scope Creep:** The conversational nature might lead to users expecting capabilities beyond the defined scope.
*   **Performance:** Re-triggering predictions for parts of the tree could be time-consuming; managing user expectations for response times.
*   **Error Handling:** Robustly handling invalid user commands or unexpected failures during prediction regeneration.

## 7. Development Phases/Milestones (High-Level)
1.  **Phase 1: Core Q&A & Setup**
    *   Develop basic Chat UI.
    *   Implement State Manager for futurecast data.
    *   Implement NLU for basic question intents.
    *   Integrate LLM Interaction Layer for answering questions based on current futurecast context.
2.  **Phase 2: Effect Modification**
    *   Extend NLU to recognize "modify effect" intents and extract parameters.
    *   Implement logic in Action Dispatcher to update effect text in State Manager.
    *   Integrate with Prediction Engine Interface to re-trigger downstream predictions.
3.  **Phase 3: Effect Expansion**
    *   Extend NLU for "expand effect" intents.
    *   Implement logic to call Prediction Engine for targeted expansion.
    *   Integrate new effects into the State Manager and UI.
4.  **Phase 4: Refinement & Testing**
    *   Improve error handling and user feedback mechanisms.
    *   Conduct thorough testing of all functionalities.
    *   UI/UX polishing.
5.  **Phase 5: Deployment & Iteration**
    *   Deploy MVP.
    *   Gather user feedback for future enhancements.

## 8. Detailed Implementation Plan / Task Breakdown
This section will be expanded to outline specific development tasks, sub-tasks, assignments, and checklists for each phase. It can be managed as a separate linked document or using project management tools (e.g., Task Master, Linear, Jira) to track progress.

## 9. Open Questions & Assumptions
*   **Assumptions:**
    *   The existing `PredictionEngine` can be adapted to support targeted re-predictions and expansions without major architectural changes.
    *   The primary application LLM is suitable for both Q&A and instruction-following for modification/expansion tasks.
    *   Users will primarily interact with one futurecast at a time within the chatbot context.
    *   A simple rule-based or keyword-based NLU will be sufficient for MVP, deferring complex intent recognition.
*   **Open Questions:**
    *   What is the acceptable latency for chatbot responses, especially when re-predictions are involved?
    *   How will the chatbot handle ambiguous instructions or requests that could have multiple interpretations?
    *   What level of detail is required for the chatbot to confirm actions before executing them (e.g., "Do you want to change X to Y?")?
    *   How will errors from the prediction engine be communicated back to the user through the chat interface?
    *   What are the specific formats for identifying effects in chat (e.g., by ID, by text, by position)?
    *   Will the initial version require a visual indication on the effect tree of which node is being discussed or modified by the chatbot?