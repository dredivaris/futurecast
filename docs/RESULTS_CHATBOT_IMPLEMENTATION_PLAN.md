## 8. Detailed Implementation Plan / Task Breakdown

This section outlines specific development tasks, sub-tasks, and checklists for each phase of the Results Chatbot development.

Key:
[x] for fully completed tasks.
[/] for partially or implicitly completed tasks (e.g., some testing done during development, but formal test suites might not be exhaustive yet).
[~] for tasks that are not applicable or were addressed differently (e.g., separate backend API for Streamlit).

### Phase 1: Core Q&A & Setup
*Goal: Establish the foundational components for chat interaction and information retrieval from the futurecast.*

*   **1.1. Develop Basic Chat UI**
    *   [x] 1.1.1. **Design:**
        *   [x] 1.1.1.1. Mockup chat window interface (input field, message display area, send button).
        *   [x] 1.1.1.2. Define basic styling, theme, and responsiveness considerations.
    *   [x] 1.1.2. **Frontend Implementation (e.g., Streamlit, custom web component):**
        *   [x] 1.1.2.1. Implement message display area to render user and chatbot messages chronologically.
        *   [x] 1.1.2.2. Implement user text input field with appropriate size and behavior.
        *   [x] 1.1.2.3. Implement "Send" button functionality and/or Enter key submission.
        *   [x] 1.1.2.4. Develop frontend logic to handle message submission, clear input field, and update message display.
        *   [x] 1.1.2.5. Ensure UI automatically scrolls to show the latest messages.
        *   [x] 1.1.2.6. Basic error display on UI for connection issues.
        *   [x] 1.1.2.7. Integrate Chatbot UI directly below the summary section in the main application view.
    *   [~] 1.1.3. **API Integration (Backend Communication):**
        *   [~] 1.1.3.1. Define API endpoint contract (request/response format) for sending user messages and receiving chatbot responses. (N/A for direct Streamlit integration)
        *   [~] 1.1.3.2. Implement frontend JavaScript/Python to make asynchronous calls to this API. (N/A for direct Streamlit integration)
*   **1.2. Implement State Manager for Futurecast Data**
    *   [x] 1.2.1. **Design:**
        *   [x] 1.2.1.1. Define Python data structures/classes for storing:
            *   [x] Initial seed prompt (text).
            *   [x] Effect tree (e.g., list of nodes with ID, parent ID, text, children IDs).
            *   [x] Results summary (text).
        *   [x] 1.2.1.2. Consider data structure for chat history (user message, bot response, timestamp) - (Note: Full saving/loading is out of MVP scope, but in-memory history for current session is useful).
    *   [x] 1.2.2. **Implementation (`StateManager` class/module):**
        *   [x] 1.2.2.1. Create `StateManager` class.
        *   [x] 1.2.2.2. Implement method to load/initialize futurecast data (from main application or a defined source).
        *   [x] 1.2.2.3. Implement methods to access/query futurecast data (e.g., `get_effect_by_id(id)`, `get_all_effects_text()`, `get_summary_text()`, `get_initial_prompt()`).
        *   [x] 1.2.2.4. Implement methods to retrieve context for the LLM (e.g., a concatenated string of relevant futurecast data).
        *   [x] 1.2.2.5. Ensure basic data validation on load.
*   **1.3. Implement NLU for Basic Question Intents**
    *   [x] 1.3.1. **Design:**
        *   [x] 1.3.1.1. Define initial set of question intents (e.g., `ask_general_summary`, `ask_about_specific_effect_text`, `ask_about_initial_prompt`, `ask_about_economic_impacts`).
        *   [x] 1.3.1.2. Design rule-based or keyword-spotting logic for intent recognition (e.g., "what is", "tell me about", "explain effect").
        *   [x] 1.3.1.3. Define simple entity extraction if needed (e.g., keywords from the question to help narrow down context for the LLM).
    *   [x] 1.3.2. **Implementation (`NLUProcessor` class/module):**
        *   [x] 1.3.2.1. Create `NLUProcessor` class.
        *   [x] 1.3.2.2. Implement intent recognition logic based on designed rules/keywords.
        *   [x] 1.3.2.3. Implement basic entity extraction.
        *   [x] 1.3.2.4. Define output format (e.g., `{"intent": "ask_about_specific_effect_text", "entities": {"effect_keywords": ["technology adoption"]}}`).
*   **1.4. Integrate LLM Interaction Layer for Answering Questions**
    *   [x] 1.4.1. **Design:**
        *   [x] 1.4.1.1. Define prompt structures for different question intents, instructing the LLM to synthesize answers from provided context.
        *   [x] 1.4.1.2. Determine how much context from `StateManager` to pass to LLM for Q&A to balance relevance and token limits.
    *   [x] 1.4.2. **Implementation (`LLMInteraction` class/module):**
        *   [x] 1.4.2.1. Create `LLMInteraction` class.
        *   [x] 1.4.2.2. Implement method to formulate prompts for Q&A based on recognized intent and context retrieved from `StateManager`.
        *   [x] 1.4.2.3. Implement method to call the primary application LLM API.
        *   [x] 1.4.2.4. Implement method to parse LLM response and format it for the Chat UI.
        *   [x] 1.4.2.5. Ensure LLM provides full and complete responses.
*   **1.5. Implement Action Dispatcher (Initial Version for Q&A)**
    *   [x] 1.5.1. **Design:**
        *   [x] 1.5.1.1. Define logic to route recognized intents from NLU to appropriate handlers/actions.
    *   [x] 1.5.2. **Implementation (`ActionDispatcher` class/module):**
        *   [x] 1.5.2.1. Create `ActionDispatcher` class.
        *   [x] 1.5.2.2. Implement core logic:
            *   [x] Receive NLU output.
            *   [x] If Q&A intent, retrieve context via `StateManager`.
            *   [x] Call `LLMInteraction` with context and intent to get an answer.
            *   [x] Return formatted answer.
*   **1.6. Backend API Endpoint for Chat**
    *   [~] 1.6.1. **Implementation (e.g., using Flask/FastAPI if Python backend):** (N/A for direct Streamlit integration)
        *   [~] 1.6.1.1. Develop a backend API endpoint that:
            *   [~] Accepts user message (e.g., JSON payload).
            *   [~] Initializes/accesses `StateManager`, `NLUProcessor`, `ActionDispatcher`, `LLMInteraction`.
            *   [~] Passes message to `NLUProcessor`.
            *   [~] Passes NLU output to `ActionDispatcher`.
            *   [~] Returns chatbot's response (e.g., JSON payload).
*   **1.7. Basic Testing & Integration (Phase 1)**
    *   [/] 1.7.1. Unit tests for `StateManager` (load, access methods). (Implicitly tested)
    *   [/] 1.7.2. Unit tests for `NLUProcessor` (intent recognition for defined Q&A intents). (Implicitly tested)
    *   [/] 1.7.3. Unit tests for `LLMInteraction` (prompt formulation, mock LLM call). (Implicitly tested)
    *   [/] 1.7.4. Unit tests for `ActionDispatcher` (routing Q&A intents). (Implicitly tested)
    *   [x] 1.7.5. Integration test for the complete Q&A flow: Chat UI -> Backend API -> NLU -> Action Dispatcher -> StateManager -> LLMInteraction -> Response -> Chat UI. (Streamlit app serves as integration)
    *   [x] 1.7.6. Test basic Q&A scenarios with sample futurecast data.

### Phase 2: Effect Modification
*Goal: Enable users to modify the text of existing effects in the futurecast tree via chat, and see downstream effects regenerated.*

*   **2.1. Extend NLU for "Modify Effect" Intents**
    *   [x] 2.1.1. **Design:**
        *   [x] 2.1.1.1. Define "modify_effect" intent.
        *   [x] 2.1.1.2. Define necessary entities to extract:
            *   [x] Effect identifier (e.g., a unique ID if available, or a text snippet of the effect to be modified).
            *   [x] New effect text.
        *   [x] 2.1.1.3. Design NLU logic (rules/keywords) for intent and entity extraction (e.g., "change effect 'X' to 'Y'", "modify 'X' and make it 'Y'").
        *   [x] 2.1.1.4. Consider how to handle ambiguity if multiple effects match a text snippet. (MVP: may require exact match or ask for clarification).
    *   [x] 2.1.2. **Implementation (`NLUProcessor`):**
        *   [x] 2.1.2.1. Update `NLUProcessor` to recognize "modify_effect" intent.
        *   [x] 2.1.2.2. Implement entity extraction for effect identifier and new text.
*   **2.2. Implement Logic in Action Dispatcher for Modification**
    *   [x] 2.2.1. **Design:**
        *   [x] 2.2.1.1. Define workflow for "modify_effect" intent:
            *   [x] Use effect identifier from NLU to find the target effect in `StateManager`.
            *   [ ] (Optional) Confirm action with user: "Are you sure you want to change effect 'Old Text' to 'New Text'?" (Not implemented, direct action)
            *   [x] Update the effect's text in `StateManager`.
            *   [x] Prepare data for `PredictionEngineInterface` (e.g., ID of modified node, current tree state).
            *   [x] Call `PredictionEngineInterface` to re-trigger downstream predictions.
            *   [x] Receive updated downstream effects.
            *   [x] Update `StateManager` with these new downstream effects.
            *   [x] Formulate confirmation/status message for UI (e.g., "Effect updated. Downstream effects regenerated.").
    *   [x] 2.2.2. **Implementation (`ActionDispatcher`):**
        *   [x] 2.2.2.1. Update `ActionDispatcher` to handle "modify_effect" intent.
        *   [x] 2.2.2.2. Implement logic to interact with `StateManager` to find and update effect text.
        *   [x] 2.2.2.3. Implement logic to call `PredictionEngineInterface`.
        *   [x] 2.2.2.4. Implement logic to update `StateManager` with results from prediction engine.
*   **2.3. Implement Prediction Engine Interface (Modification)**
    *   [x] 2.3.1. **Design:**
        *   [x] 2.3.1.1. Define interface/method in `PredictionEngineInterface` module/class to accept:
            *   [x] ID of the modified effect.
            *   [x] The full current effect tree (or relevant portion needed by `PredictionEngine`).
            *   [x] New text of the modified effect.
        *   [x] 2.3.1.2. Define expected output: a list/tree of regenerated downstream effects.
        *   [x] 2.3.1.3. Clarify if `PredictionEngine` can take the modified node and regenerate *only* its children and further descendants. (Simulated as such)
    *   [x] 2.3.2. **Implementation (`PredictionEngineInterface`):**
        *   [x] 2.3.2.1. Create/Update `PredictionEngineInterface` module/class.
        *   [x] 2.3.2.2. Implement method to call the existing `PredictionEngine` with necessary parameters to regenerate downstream effects from the modified node. (Simulated)
        *   [x] 2.3.2.3. Handle communication with `PredictionEngine` (synchronous/asynchronous, error handling). (Simulated)
*   **2.4. Update State Manager for Modifications**
    *   [x] 2.4.1. **Implementation (`StateManager`):**
        *   [x] 2.4.1.1. Add/enhance method to update a specific effect's text, given its ID. (`update_effect_text_and_regenerate`)
        *   [x] 2.4.1.2. Add method to replace/update a branch of effects (i.e., remove old children of modified node and add new ones). (`update_effect_tree`)
*   **2.5. UI/UX for Modification**
    *   [x] 2.5.1. **Design:**
        *   [x] 2.5.1.1. How to clearly confirm the modification action with the user. (Via chat response)
        *   [x] 2.5.1.2. How to display status during re-prediction (e.g., "Updating effects, this may take a moment..."). (Spinner)
        *   [x] 2.5.1.3. How to indicate changes in the main futurecast display (if it's a separate visual component from the chat). (Tree updates, reflected in UI tabs)
    *   [x] 2.5.2. **Implementation (Chat UI):**
        *   [x] 2.5.2.1. Implement display of confirmation messages before action (if designed). (Post-action confirmation)
        *   [x] 2.5.2.2. Implement display of status messages during and after modification.
*   **2.6. Testing & Integration (Phase 2)**
    *   [/] 2.6.1. Unit tests for new NLU logic for "modify_effect". (Implicitly tested)
    *   [/] 2.6.2. Unit tests for `ActionDispatcher` modification path. (Implicitly tested)
    *   [/] 2.6.3. Unit tests for `PredictionEngineInterface` modification method (mocking `PredictionEngine`). (Implicitly tested)
    *   [/] 2.6.4. Unit tests for `StateManager` update methods related to modification. (Implicitly tested)
    *   [x] 2.6.5. Integration test for the full "modify effect" flow: UI -> NLU -> Action Dispatcher -> State Manager -> Prediction Engine Interface -> Prediction Engine (mocked/real) -> State Manager -> UI. (Streamlit app serves as integration)
    *   [x] 2.6.6. Test various modification scenarios (e.g., modifying an effect with children, modifying a leaf effect).
    *   [x] 2.6.7. Test error handling (e.g., effect not found, `PredictionEngine` failure during regeneration).

### Phase 3: Effect Expansion
*Goal: Allow users to select a leaf effect and request the chatbot to expand it by generating further downstream effects.*

*   **3.1. Extend NLU for "Expand Effect" Intents**
    *   [x] 3.1.1. **Design:**
        *   [x] 3.1.1.1. Define "expand_effect" intent.
        *   [x] 3.1.1.2. Define necessary entities to extract:
            *   [x] Leaf effect identifier (e.g., ID, unique text snippet).
            *   [x] Number of levels to expand (optional, with a default value, e.g., 1 or 2 levels).
            *   [x] Focus/context for expansion (optional, e.g., "focusing on economic impacts").
        *   [x] 3.1.1.3. Design NLU logic for intent and entity extraction (e.g., "expand effect 'X'", "add 2 levels to 'X' about 'Y'").
    *   [x] 3.1.2. **Implementation (`NLUProcessor`):**
        *   [x] 3.1.2.1. Update `NLUProcessor` to recognize "expand_effect" intent.
        *   [x] 3.1.2.2. Implement entity extraction for effect identifier, expansion levels, and focus.
*   **3.2. Implement Logic in Action Dispatcher for Expansion**
    *   [x] 3.2.1. **Design:**
        *   [x] 3.2.1.1. Define workflow for "expand_effect" intent:
            *   [x] Identify target leaf effect in `StateManager`. (Error if not a leaf node).
            *   [ ] (Optional) Confirm action with user. (Not implemented, direct action)
            *   [x] Prepare data for `PredictionEngineInterface` (target node ID, expansion parameters).
            *   [x] Call `PredictionEngineInterface` for targeted expansion.
            *   [x] Receive new child effects.
            *   [x] Integrate new child effects into `StateManager` under the target parent.
            *   [x] Formulate confirmation/status message for UI.
    *   [x] 3.2.2. **Implementation (`ActionDispatcher`):**
        *   [x] 3.2.2.1. Update `ActionDispatcher` to handle "expand_effect" intent.
        *   [x] 3.2.2.2. Implement logic to validate if the target effect is a leaf node.
        *   [x] 3.2.2.3. Implement logic to call `PredictionEngineInterface` with expansion parameters.
        *   [x] 3.2.2.4. Implement logic to update `StateManager` with newly generated effects.
*   **3.3. Implement Prediction Engine Interface (Expansion)**
    *   [x] 3.3.1. **Design:**
        *   [x] 3.3.1.1. Define interface/method in `PredictionEngineInterface` to accept:
            *   [x] ID of the target leaf effect to expand.
            *   [x] Expansion parameters (e.g., depth, focus/prompt for expansion).
            *   [x] The full current effect tree.
        *   [x] 3.3.1.2. Define expected output: a list/tree of new child effects for the target node.
        *   [x] 3.3.1.3. Clarify how `PredictionEngine` handles targeted expansion requests. (Simulated)
    *   [x] 3.3.2. **Implementation (`PredictionEngineInterface`):**
        *   [x] 3.3.2.1. Update `PredictionEngineInterface` module/class.
        *   [x] 3.3.2.2. Implement method to call the existing `PredictionEngine` to generate new child effects for the specified node based on expansion parameters. (Simulated)
        *   [x] 3.3.2.3. Handle communication with `PredictionEngine`. (Simulated)
*   **3.4. Update State Manager for Expansions**
    *   [x] 3.4.1. **Implementation (`StateManager`):**
        *   [x] 3.4.1.1. Add method to `StateManager` to add new child effects to a specified parent node, ensuring tree integrity. (`update_effect_tree`)
*   **3.5. UI/UX for Expansion**
    *   [x] 3.5.1. **Design:**
        *   [x] 3.5.1.1. How to confirm expansion action and parameters with the user. (Via chat response)
        *   [x] 3.5.1.2. How to display status during expansion generation. (Spinner)
        *   [x] 3.5.1.3. How new effects are reflected in the main futurecast display. (Tree updates, reflected in UI tabs)
    *   [x] 3.5.2. **Implementation (Chat UI):**
        *   [x] 3.5.2.1. Implement display of confirmation and status messages for expansion.
*   **3.6. Testing & Integration (Phase 3)**
    *   [/] 3.6.1. Unit tests for new NLU logic for "expand_effect". (Implicitly tested)
    *   [/] 3.6.2. Unit tests for `ActionDispatcher` expansion path, including validation (e.g., is_leaf). (Implicitly tested)
    *   [/] 3.6.3. Unit tests for `PredictionEngineInterface` expansion method (mocking `PredictionEngine`). (Implicitly tested)
    *   [/] 3.6.4. Unit tests for `StateManager` update methods related to expansion. (Implicitly tested)
    *   [x] 3.6.5. Integration test for the full "expand effect" flow: UI -> NLU -> Action Dispatcher -> Prediction Engine Interface -> Prediction Engine (mocked/real) -> State Manager -> UI. (Streamlit app serves as integration)
    *   [x] 3.6.6. Test various expansion scenarios (different depths, with/without focus text).
    *   [x] 3.6.7. Test error handling (e.g., trying to expand a non-leaf node, `PredictionEngine` failure).

### Phase 4: Refinement & Testing
*Goal: Enhance robustness, user experience, and ensure all MVP features are thoroughly tested.*

*   **4.1. Improve Error Handling and User Feedback Mechanisms**
    *   [x] 4.1.1. **Review and Design:**
        *   [x] 4.1.1.1. Systematically review all potential error points across Q&A, modification, and expansion flows (NLU misinterpretation, effect not found, `PredictionEngine` errors, LLM errors).
        *   [x] 4.1.1.2. Design clear, concise, and user-friendly error messages for each scenario.
        *   [x] 4.1.1.3. Design improved feedback mechanisms for successful operations and for indicating ongoing processes (e.g., loading spinners, progress messages).
    *   [x] 4.1.2. **Implementation:**
        *   [x] 4.1.2.1. Implement robust error handling (try-except blocks, validation checks) in `NLUProcessor`, `ActionDispatcher`, `LLMInteraction`, `PredictionEngineInterface`, and backend API.
        *   [x] 4.1.2.2. Ensure errors are caught gracefully and propagated correctly to the Chat UI with user-friendly messages.
        *   [x] 4.1.2.3. Refine all chatbot messages (confirmations, status updates, errors) for clarity, conciseness, and consistent tone.
        *   [x] 4.1.2.4. Implement visual loading indicators or progress updates in the Chat UI for operations that may take time (e.g., re-predictions, expansions).
*   **4.2. Conduct Thorough Testing of All Functionalities**
    *   [ ] 4.2.1. **Test Planning:**
        *   [ ] 4.2.1.1. Develop a comprehensive test plan covering all MVP features and their interactions.
        *   [ ] 4.2.1.2. Define detailed test cases for Q&A, modification, and expansion, including:
            *   Happy path scenarios.
            *   Edge cases (e.g., empty inputs, very long inputs, special characters).
            *   Error conditions (e.g., invalid commands, non-existent effects).
            *   NLU robustness with diverse user phrasings for each intent.
    *   [ ] 4.2.2. **Execution:**
        *   [ ] 4.2.2.1. Execute all defined unit tests for all modules.
        *   [ ] 4.2.2.2. Execute all defined integration tests for end-to-end flows.
        *   [ ] 4.2.2.3. Perform manual/exploratory testing of the chat interface, focusing on usability and uncovering unhandled scenarios.
        *   [ ] 4.2.2.4. Test with various futurecast structures and complexities (small trees, large trees).
        *   [ ] 4.2.2.5. Test concurrent operations if applicable (though likely single-threaded for MVP).
    *   [ ] 4.2.3. **Bug Fixing:**
        *   [ ] 4.2.3.1. Log all identified bugs in a tracking system.
        *   [ ] 4.2.3.2. Prioritize and fix critical/high-priority bugs for MVP.
*   **4.3. UI/UX Polishing**
    *   [ ] 4.3.1. **Review and Feedback:**
        *   [ ] 4.3.1.1. Conduct internal UI/UX review sessions.
        *   [ ] 4.3.1.2. If possible, get preliminary feedback from a small group of test users.
        *   [ ] 4.3.1.3. Focus on chat flow intuitiveness, clarity of chatbot messages, ease of invoking commands, and overall visual appeal.
    *   [ ] 4.3.2. **Implementation:**
        *   [ ] 4.3.2.1. Make necessary adjustments to Chat UI layout, styling, fonts, colors, and responsiveness based on feedback.
        *   [ ] 4.3.2.2. Improve wording and formatting of all chatbot messages.
        *   [ ] 4.3.2.3. Ensure a consistent visual design and interaction pattern.
*   **4.4. Documentation (Internal)**
    *   [ ] 4.4.1. **Review and Update:**
        *   [ ] 4.4.1.1. Review and update existing internal documentation for all components (`StateManager`, `NLUProcessor`, `LLMInteraction`, `ActionDispatcher`, `PredictionEngineInterface`, Backend API).
        *   [ ] 4.4.1.2. Add sequence diagrams or flowcharts for key operations (Q&A, modify, expand).
        *   [ ] 4.4.1.3. Document NLU intent definitions, entity extraction rules, and LLM prompt strategies.
        *   [ ] 4.4.1.4. Document error codes/types and their meanings.

### Phase 5: Deployment & Iteration
*Goal: Deploy the MVP of the Results Chatbot and establish a process for gathering feedback for future improvements.*

*   **5.1. Prepare for Deployment (MVP)**
    *   [ ] 5.1.1. **Environment Setup & Configuration:**
        *   [ ] 5.1.1.1. Configure staging and production environments (if separate).
        *   [ ] 5.1.1.2. Ensure all dependencies (Python packages, LLM API keys, etc.) are correctly managed and secured.
        *   [ ] 5.1.1.3. Set up logging and monitoring for the chatbot service.
    *   [ ] 5.1.2. **Final Checks:**
        *   [ ] 5.1.2.1. Perform a final round of smoke testing in the staging/production-like environment.
        *   [ ] 5.1.2.2. Verify all configuration settings are correct for the target environment.
        *   [ ] 5.1.2.3. Review security considerations (e.g., input sanitization, API authentication if applicable).
    *   [ ] 5.1.3. **Deployment Plan:**
        *   [ ] 5.1.3.1. Outline detailed deployment steps.
        *   [ ] 5.1.3.2. Prepare a rollback plan in case of critical issues post-deployment.
*   **5.2. Deploy MVP**
    *   [ ] 5.2.1. Execute the deployment plan.
    *   [ ] 5.2.2. Monitor the application closely immediately after deployment for any errors or performance issues.
    *   [ ] 5.2.3. Announce availability to target users/stakeholders.
*   **5.3. Gather User Feedback**
    *   [ ] 5.3.1. **Establish Feedback Mechanisms:**
        *   [ ] 5.3.1.1. Implement or integrate a basic feedback mechanism within the application (e.g., a "Feedback" button linking to a form or email).
        *   [ ] 5.3.1.2. Plan for direct user testing sessions or interviews with early adopters if feasible.
    *   [ ] 5.3.2. **Collection & Analysis Process:**
        *   [ ] 5.3.2.1. Define a process for systematically collecting and organizing user feedback.
        *   [ ] 5.3.2.2. Regularly review and analyze feedback to identify common pain points, frequently requested features, and general usability issues.
*   **5.4. Plan for Future Iterations**
    *   [ ] 5.4.1. **Backlog Grooming:**
        *   [ ] 5.4.1.1. Review the "Out of Scope (Future Enhancements)" list from the planning document.
        *   [ ] 5.4.1.2. Incorporate new feature requests and improvements identified from user feedback into a product backlog.
    *   [ ] 5.4.2. **Prioritization & Roadmapping:**
        *   [ ] 5.4.2.1. Prioritize backlog items based on user value, technical feasibility, and strategic goals.
        *   [ ] 5.4.2.2. Outline a roadmap for the next 1-2 development cycles.
*   **5.5. Documentation (User-Facing, if any for MVP)**
    *   [ ] 5.5.1. **Content Creation:**
        *   [ ] 5.5.1.1. Prepare a brief user guide, FAQ, or tooltips explaining how to use the chatbot's core features (Q&A, modify, expand).
        *   [ ] 5.5.1.2. Include examples of effective chat commands.
    *   [ ] 5.5.2. **Accessibility:**
        *   [ ] 5.5.2.1. Make user documentation easily accessible from within the application.