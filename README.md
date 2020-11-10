## What is NodCast

Using NodCast you can search, study and manage scientific papers or any other article.

However, the main goal of NodCast is to provide a new experience of study. The program is text-based and relies mainly on the keyboard. The program offers you the summaries of the articles when you want to concentrate on the purpose and main ideas within an article. You can also view the figures of the article in a browser. If you want to access the original article, you can download and open the original pdf file for each article.

## Installation

Installation on linux:
```
pip install nodcast
```
### Installation on Windows
For Windows you need to instll `windows-curses` package too, so use the following command:
```
pip install windows-curses nodcast
```

## Nods
Nods are feedbacks you give to a sentence or a portion of text. It resembles the way you listen to the talks of a lecturer. You may admit what you've heard with 'okay, yes, etc.' or you may have a problem in getting the purpose of a sentence.
When you open an article and start reading, NodCast automatically highlights the first sentence of an article. To expand the selection to more sentences press the `<Down>` arrow key. After selecting and reading a fragment of text (a paragraph or a certain number of sentences) you need to provide a Nod to be able to move to the next part. 

Example of nodes are:

#### Positive nods: 
 - **okay**, when you have almost understood the purpose of a sentence or a fragment of the text
 - **I see!**, when you have completely understood the meaning and purpose of a sentence and you admit it.
 - **interesting!**, when you found the sentence or paragraph has a useful point.
 - **important!**, when you think it contains an important point that can be useful for you.

#### Negative nods: 
 - **okay so?**, when you understand the meaning of a sentence but you don't know its purpose and you are waiting for a complementary sentence or paragraph.
 - **didn't get, but okay**, when you didn't get the purpose or meaning of a sentence, but it's not currently important for you and you can continue.
 - **didn't get**, when you didn't get the purpose or meaning of a sentence, and you are confused.
 - **needs research** when there are some points or jargon in the sentence that needs to be researched.
  

### How to enter a nod

For positive nods, press the `<Right>` arrow key once or multiple times. They appear in order with each keystroke. For negative nods, do the same but with `<Left>` arrow key. After entering a nod press the `<Down>` arrow key to move to the next sentence. 

### Categorizing articles

After reading a part of an article, you can similarly enter a nod for the whole article, such as "important, interesting, review later, etc.". To do this, press `<left>` arrow key when the title is selected (press `<Home>` to select it). These nods shows your understanding of the article's content and are used to categorize articles under "reviewed articles" section. You can also add tags to articles, which are again used to manage the articles under "saved items" section. 


## Comments and notes

Sometimes you want to add a comment to the selected fragment. To do this, press `:` (colon). Then you can write your comment in a bar that appears below the article. Hit `<Enter>` to enter the comment.

### Multiple lines comments

The bar shown below the article has the capacity of a single line note. If you want to add more lines, press right angle bracket (`>`) to insert a new line after the current line. You can then use arrow keys to navigate between the lines. Press left angle bracket (`<`) to remove a line. 


## other features

NodCast has many other features, which you can discover when you are working with it. Some hotkeys are listed below. They are accessible when you open an article. You can press `h` to see the list of available command in each section. 

```
 Down)          expand the selection to the next sentence
 Right)         nod the selected sentences with the positie nods
 Right)         nod the selected sentences with the negative nods
 o)             download/open pdf file externally
 f)             list figures
 t)             tag the article
 d)             delete the external pdf file 
 w)             write the article into a file
 p)             select an output file format
 m)             change the color theme
 u)             reset comments and nods
 DEL)           remove the current nod from the selected sentence
 n)             filter the sentences by a nod
 +/-)           increase/decrease the width of the text
 :)             add a comment to the selected fragment
 k/j)           previous/next section
 l/;)           previous/next fragment
 PgUp/PgDown)   previous/next page
 h)             show this list
 q)             close
```

###  working with menus and input boxes

Press `<Down>` or `<Up>` keys to navigate between the items of a menu. Optionally, you can press the hotkey associated with each item which is shown at the beginning of that option. Press `<Enter>` to open or run a menu item. Some items are input boxes like keywords for a search menu item. To escape an input box, you can either use `<Esc>` or simply `<Down>` key to move to the next item. Another useful key in the input box is left angle bracket (`<` which clears the entire input box.


## Accessing website articles or opening a webpage

If you want to fetch and read the articles of a website, or a specific webpage, you can install `newspaper3k`. 

```
pip install newspaper3k
```

Then, when you start NodCast, two new options are added to the main menu, namely `website articles` and `webpage`.  
 
 

