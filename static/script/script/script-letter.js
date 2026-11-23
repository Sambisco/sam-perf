 let optionsButtons = document.querySelectorAll(".option-button");
 let advancedOptionsButtons = document.querySelectorAll(".adv-option-button");
 let fontName = document.getElementById("fontName");
 let fontSizeRef = document.getElementById("fontSize");
 let writingArea = document.getElementById("text-input");
 let linkButton = document.getElementById("createLink");
 let alignButtons = document.querySelectorAll(".align");
 let spacingButtons = document.querySelectorAll(".spacing");
 let formatButtons = document.querySelectorAll(".format");
 let scriptButtons = document.querySelectorAll(".script");

 // List of fontlist
 let fontlist = [
     "Arial",
     "Verdana",
     "Times New Roman",
     "Garamond",
     "Georgia",
     "Courier New",
     "cursive"
 ];

 // initial Setting
 const initializer = () => {
     //fonction qui appelle tous les highlighting buttons
     // No highlights for link, unlink,lists, undo,redo depuis ils sont sur le meme temps d'opération
     highlighter(alignButtons, true);
     highlighter(spacingButtons, true);
     highlighter(formatButtons, false);
     highlighter(scriptButtons, true);

     //create option for font names
     fontlist.map((value) => {
         let option = document.createElement("option");
         option.value = value;
         option.innerHTML = value;
         fontName.appendChild(option)
     });

     //FontSize allows only till 7
     for (let i = 1; i <= 7; i++) {
         let option = document.createElement("option");
         option.value = i;
         option.innerHTML = i;
         fontSizeRef.appendChild(option)
     }

     //Default size
     fontSizeRef.value = 3;
 };

 // Main logic
 const modifyText = (command, defaultUI, value) => {
     // execCoùùand executes command on selected text
     document.execCommand(command, defaultUI, value)
 };

 // for basic operations which don't need value parameter
 optionsButtons.forEach((button) => {
     button.addEventListener("click", () => {
         modifyText(button.id, false, null)
     })
 });

 // options that require value parameter (e.g colors,fonts)
 advancedOptionsButtons.forEach((button) => {
     button.addEventListener("change", () => {
         modifyText(button.id, false, button.value)
     });
 });

 //LINK
 linkButton.addEventListener("click", () => {
     let userLink = prompt("Entrer un url");
     // if link has http then pass directly else add https
     if (/http/i.test(userLink)) {
         modifyText(linkButton.id, false, userLink)
     } else {
         userLink = "http://" + userLink;
         modifyText(linkButton.id, false, userLink)

     }
 });

 //Highlight clicked button
 const highlighter = (className, needsRemoval) => {
     className.forEach((button) => {
         button.addEventListener("click", () => {
             // needsRemoval =true means only one button should be highlight and other would be normal
             if (needsRemoval) {
                 let alreadyActive = false;

                 // if currently clicked button is already active
                 if (button.classList.contains("activeLetter")) {
                     alreadyActive = true;
                 }

                 // Remove highlight from other buttons
                 highlighterRemover(className);
                 if (!alreadyActive) {
                     //highlight clicked button
                     button.classList.add("activeLetter")
                 }
             } else {
                 // if other buttons can be highlighted
                 button.classList.toggle("activeLetter")
             }
         });
     });
 };

 const highlighterRemover = (className) => {
     className.forEach((button) => {
         button.classList.remove("activeLetter");
     })
 }
 window.onload = initializer();