# aspectj-activeness
Describes my execution and attachments for the research seminar project. In this project I analyzed the activeness of AspectJ repositories. AspectJ is an Aspect Oriented programming language. Aspect Oriented Programming (AOP) is a programming paradigm in which concerns of a system are separately specified with some description of their relationships. To accomplish this a programmer can rely on the mechanisms of an underlying AOP environment to weave or compose these concepts together into coherent programs. The weaving of these concepts into source code is done without changing the actual code of the program. The idea is that this weaving is done via pointcuts and join points. A join point is a step in the program execution such as a method or an exception handling. A pointcut is a means of referring to a collection of join points via predicates.

When moving crosscutting concerns from to aspects we are essentially moving our code from a source file to a new aspect file. To help with a seamless integration support in language features is very useful. AspectJ is one of languages, most AOP languages are actually just extensions on existing languages as AspectJ is an extension on the Java programming language.

The activeness is based on 4 measurements:
- **Number of commits:** combines the total amount of commits for every month between January 2016 and April 2021. Commits can give an insight in how much the code is being changed in certain months.
- **Number of changes:**  combines the total amount of changes for every month between January 2016 and April 2021. In this case a change is either a line deletion or an insertion in a commit. This can give an insight in how much code there is created for the AspectJ repositories.
- **Number of files:**  combines the total amount of files changed for every month between January 2016 and April 2021. For every commit the amount of files changed is counted, this can be used to indicate how much the files are updated.
- **Number of issues:**  combine the total amount of issues based on the creation date for every month between January 2016 and April 2021. This gives in insight in how active the issues of a repository are.

## Code
The code can be found in the code folder, for this to be able to be run a config.ini file must be created providing your GitHub search API key.
```
[auth]
token = 'enter your token here'
```
In the code the functions can be used to fetch the data. You can just call a function in the main and the fetching will execute, be aware that the repository mining can take quite some time.

## Data
The retrieved data can be found in the data folder. This contains the results of the activeness measurements which were applied on the AspectJ repositories.
