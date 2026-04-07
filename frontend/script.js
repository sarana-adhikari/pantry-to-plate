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

        // NEW: If the backend throws a 400 or 500 error, display it gracefully!
        if (!response.ok) {
            recipeOutput.innerHTML = `<span style="color: #ef4444; font-weight: bold;">Oops!</span> ${data.error}`;
            return;
        }

        // If successful, display the recipe
        recipeOutput.innerHTML = data.recipe.replace(/\n/g, '<br>');
        
    } catch (error) {
        // This only triggers if the internet goes down or the URL is completely broken
        recipeOutput.innerHTML = "Error: Could not connect to the server.";
    } finally {
        loading.classList.add('hidden');
    }
});
