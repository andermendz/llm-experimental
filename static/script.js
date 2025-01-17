document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('prompt-form');
    const textarea = document.getElementById('user-input');
    const submitButton = document.getElementById('submit-button');
    const outputArea = document.getElementById('output-area');
    const loadingIndicator = document.getElementById('loading');
    const exampleButtons = document.querySelectorAll('.example-button');

    async function generatePrompt(userInput) {
        loadingIndicator.style.display = 'block';
        submitButton.disabled = true;
        
        try {
            const response = await fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ user_input: userInput }),
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            outputArea.textContent = data.result;
        } catch (error) {
            console.error('Error:', error);
            outputArea.textContent = 'An error occurred while generating the prompt. Please try again.';
        } finally {
            loadingIndicator.style.display = 'none';
            submitButton.disabled = false;
        }
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const userInput = textarea.value.trim();
        if (userInput) {
            await generatePrompt(userInput);
        }
    });

    exampleButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const exampleText = button.textContent;
            textarea.value = exampleText;
            await generatePrompt(exampleText);
        });
    });
});
