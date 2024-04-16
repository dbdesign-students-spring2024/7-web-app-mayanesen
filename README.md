# Flask-MongoDB Web App

by Maya Nesen

## Cafecito

My web app is called "Cafecito". 

[Deployed copy of my web app](http://127.0.0.1:5000)

Cafecito is an app where users can read and share coffee recipes. 
- The home page contains a "Home" button to return to it, "Coffee Recipes" page to see all the recipes posted, "Coffee Reviews" for reviews of those recipes, and "Log in" to sign into your account.
- The "Coffee Recipes" page shows all recipes posted with the recipe name, the user who created it, the ingredients necessary, and the instructions. There is also a link with a form to post your own recipe which will be added to the page.
- The "Coffee Reviews" page shows all reviews posted for recipes with the recipe name it corresponds to, the user who created it, the timestamp, and the review. There is also a link with a form to post your own review which will be added to the page.
- The "Login" page allows you to sign up or log in to your account to be part of the "Cafecito community". When you login, you arrive at the user's dashboard which has the reviews and recipes that they've posted, as well as gaining the ability to edit or delete the reviews or recipes. Editing leads to forms to edit the review or recipe. The bottom of the dashboard page allows you to logout.
- The home page also has a search bar which allows you to search for recipes.


tomorrow to do : 
fix edit.html and routes for reviews
<!--NEED TO CREATE EDIT template/route AND DELETE route FOR RECIPES -->
    <a href="{{ url_for('edit', mongoid=doc._id) }}">Edit</a> |
    <a href="{{ url_for('delete', mongoid=doc._id) }}">Delete</a>
connect to i6 server?




