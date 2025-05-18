# src/futurecast/chatbot/llm_interaction.py
import logging
import google.generativeai as genai
from futurecast.config import Config

logger = logging.getLogger(__name__)

class LLMInteraction:
    """Handles interaction with the Large Language Model."""

    def __init__(self, config: Config):
        """
        Initializes the LLMInteraction component.

        Args:
            config: The application's configuration object, containing
                    LLM settings like API key, model name, etc.
        """
        self.config = config
        if self.config.api_key:
            genai.configure(api_key=self.config.api_key)
        else:
            logger.warning("LLMInteraction: API key not configured at initialization.")

    def answer_question(self, context: str, question: str) -> str:
        """
        Sends a question and relevant context to the LLM and returns its answer.

        Args:
            context: A string containing relevant information for the LLM
                     (e.g., FutureCast data, chat history).
            question: The user's question to be answered by the LLM.

        Returns:
            A string containing the LLM's response.
        """
        logger.debug(f"LLMInteraction: Received context (length: {len(context)}) and question: '{question}' for model {self.config.model_name}")

        if not self.config.api_key:
            logger.error("LLMInteraction: API key not configured. Cannot query LLM.")
            return "API key not configured. Cannot query LLM."

        # TODO: Add pre-flight check for context length limits once known for the model.
        # For example:
        # MAX_CONTEXT_LENGTH = 30000 # Example value for gemini 1.5 flash
        # if len(context) + len(question) > MAX_CONTEXT_LENGTH:
        #     logger.warning(f"Context + question length ({len(context) + len(question)}) may exceed typical limits for {self.config.model_name}.")
        #     # Potentially truncate context or return an error, depending on strategy.

        try:
            model = genai.GenerativeModel(self.config.model_name)
            prompt = f"{context}\n\nQuestion: {question}\nAnswer:"
            logger.info(f"Sending prompt to {self.config.model_name}: First 100 chars: {prompt[:100]}")
            
            # Ensure the model name is compatible, e.g., "gemini-1.5-flash-latest"
            # For some APIs, "latest" might not be directly usable or might refer to a specific version.
            # If issues persist, try a specific version string if available.
            
            response = model.generate_content(prompt)
            
            if response.parts:
                llm_answer = "".join(part.text for part in response.parts if hasattr(part, 'text'))
                logger.debug(f"LLMInteraction: Received response from {self.config.model_name}: {llm_answer[:100]}...")
                return llm_answer
            elif response.prompt_feedback and response.prompt_feedback.block_reason:
                logger.error(f"LLMInteraction: Content generation blocked. Reason: {response.prompt_feedback.block_reason}")
                return f"Content generation blocked by the API. Reason: {response.prompt_feedback.block_reason}"
            else:
                logger.error(f"LLMInteraction: Received no usable parts or text in response from {self.config.model_name}. Full response: {response}")
                return "LLM returned an empty or unparseable response."

        except Exception as e:
            logger.error(f"LLMInteraction: Error during API call to {self.config.model_name}: {e}", exc_info=True)
            return f"Error interacting with LLM: {e}"