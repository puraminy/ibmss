## What is NodReader

Using Nodreader you can search, study and manage scientific papers or any other article.

However, the main goal of Nodreader is to provide a new experience of study. The program is text-based and relies mainly on the keyboard. The program offers you the summaries of the articles when you want to concentrate on the purpose and main ideas within an article. You can also view the figures of the article in a browser. If you want to access the original article, you can download and open the original pdf file for each article.

## Installation

Installation on linux:
```
pip install nodreader
```
### Installation on Windows
For Windows you need to instll `windows-curses` package too, so use the following command:
```
pip install windows-curses nodreader
```

## Nods
Nods are feedbacks you give to a sentence or a portion of text. It resembles the way you listen to the talks of a lecturer. You may admit what you've heard with 'okay, yes, etc.' or you may have a problem in getting the purpose of a sentence.
When you open an article and start reading, Nodreader automatically highlights the first sentence of an article. To expand the selection to more sentences press the `<Down>` arrow key. After selecting and reading a fragment of text (a paragraph or a certain number of sentences) you need to provide a Nod to be able to move to the next part. 

Example of nodes are:

 - **okay**, when you have almost understood the purpose of a sentence or a fragment of the text
 - **interesting!**, when you found it has a useful point.
 - **important!**, when you think it contains an important point which can be used later.
 - **idea!** when an idea comes to your mind by reading the sentence.
 - **definition**, when you find the text an introductory or a definition for the rest of the paper.
 - **didn't get**, when you didn't get the purpose or meaning of a sentence.
 - **review later**, when you want to review the sentence later.
 - **why**, when you understand the sentence but you don't get the reasoning behind it.
 - **explain**, when you get the sentence idea but you don't know how it's implemented.
 - **needs** research, when there are some points or jargons in the sentence that needs research.
 - ...
 

And some other nods.

### How to enter a nod

Since `okay` is supposed the common nod, you can press the `<Right>` arrow key to enter it and then you can press the `<Down>` arrow key again to move to the next sentence. To enter other nods, you need to press the `<Left>` arrow key and select a Nod from a list. In any window or section press q to exit that section. 

### Categorizing articles

After you read part of an article, you can similarly add a nod for the title of the article, such as "important, interesting, review later, etc.". These shows your level of understanding the article. This nod is used to categorize articles, and they are listed under "reviewed articles" section. You also can assign tags to articles, which is again used to manage them under "saved items" section. 


## Comments and notes

Sometimes you want to add a note or a link to the selected fragment. To do this, press : (colon). Then you can write your comment in a bar shown below the article and hit Enter at the end.

**Multiple lines notes**

The bar at the bottom of an article has the capacity of a single line note. If you want to add more lines, press right angle bracket (>) to insert a new line after the current line. You can then use arrow keys to navigate between lines. Press left angle bracket (<) to remove a line. 


## other features

Nodreader has many other features, which you can discover when you work with it. Some hotkeys are listed below. They are accessible when you open an article. You can hit h to see the following list. 

```
 Down)          expand the selection to the next sentence
 Right)         nod the selected sentences with "okay"
 Left)          select from other nods
 o)             download/open pdf file externally
 f)             list figures
 t)             tag the article
 d)             delete the external pdf file 
 w)             write the article into a file
 p)             select an output file format
 m)             change the color theme
 u)             reset comments and nods
 DEL)           remove selected sentence
 v)             restore removed sentences
 n)             filter sentences by a nod
 +/-)           increase/decrease the width of text
 :)             add a comment to the selection
 k/j)           previous/next section
 l/;)           previous/next fragment
 PgUp/PgDown)   previous/next page
 h)             show this list
 q)             close
```

###  working with menus and input boxes

Use `<Down>` or `<Up>` keys to navigate between the items of a menu. Optionally, you can press the hotkey associated with each item which is shown at the beginning of that option. Press `<Enter>` to open or run a menu item. Some items are input boxes like keywords for a search menu item. To escape an input box, you can either use `<Esc>` or simply `<Down>` key to move to the next item. Another useful key in the input box is left angle bracket (<) which clears the entire input box.


## Accessing website articles or opening a webpage

If you want to fetch and read the articles of a website, or a specific webpage, you can install `newspaper3k`. 

```
pip install newspaper3k
```

Then, when you start Nodreader, two new options are added to the main menu, namely `website articles` and `webpage`.  
 
 

