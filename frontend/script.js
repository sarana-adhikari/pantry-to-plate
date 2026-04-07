const generateBtn = document.getElementById('generateBtn');
const recipeOutput = document.getElementById('recipeOutput');
const loading = document.getElementById('loading');

generateBtn.addEventListener('click', async () => {
    const input = document.getElementById('ingredientsInput').value;
    const ingredients = input.split(',').map(i => i.trim()).filter(i => i !== "");

    if (ingredients.length === 0) {
        alert("Please enter at least one ingredient!");
        return;
    }

    loading.classList.remove('hidden');
    recipeOutput.innerHTML = '';

    try {
        const response = await fetch('https://melg32pq1j.execute-api.us-east-1.amazonaws.com/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ingredients })
        });

        const data = await response.json();
        // Convert Markdown-style text from AI to simple HTML line breaks
        recipeOutput.innerHTML = data.recipe.replace(/\n/g, '<br>');
    } catch (error) {
        recipeOutput.innerHTML = "Error: Could not reach the chef.";
    } finally {
        loading.classList.add('hidden');
    }
});