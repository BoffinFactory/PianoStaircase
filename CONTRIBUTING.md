# How to Contribute

If it is not in Github you did not contribute...

Step 1, make sure you [understand how to use git and Github](https://github.com/wrightedu/Programmers-Guide-to-the-Galaxy/blob/master/Getting-Started/git.md)

This step is probably both the most critical thing that we do not teach you here in Computer Science that 
you ***must*** learn before you can contribute code to any professional project.  

That being said, feel free to use this project as a way to ease yourself into learning `git` if it is your first time.
At a minimum you should be interacting with others via comments on specific issues on the [issues page](https://github.com/BoffinFactory/PianoStaircase/issues).

This will allow you to help us move the project forward by contributing meaningful reasearch, testing, or code / examples.
Got an idea on the next steps for the project? Make a new issue!

If you already know `git` and Github, pick an issue that interests you and make a new branch!  
So long as you are working in your own branch you can't clobber someone else's work.

Pro tip: if you are going to make a branch, make sure there is a corresponding issue that you are working on
(and go ahead and add yourself to the issue).  That way everyone knows who is working on what.  Super Pro tip:
reach out to others on the same issue (or recruit others from Discord `#boffin-factory`) so you are all on the 
same page.

Step 2, you need to make sure that you know how to use Arduino IDE and how to create programs for Arduino boards. Arduino uses C++, so anyone who has taken CS3100 should have an easy time, but that ***doesn't*** mean you need to take CS3100 to be able to understand how Arduino's work or how to program them. There is an [introduction to Arduino](https://cdn.sparkfun.com/assets/3/9/d/9/e/Intro_to_Arduino_-_v30_1.pdf) from SparkFun that provides some interesting insight, including an introduction to Ohm's law, electrical concepts, and prototyping. Be prepared, though, as it's pretty in-depth for a beginner looking to do a crash-course in Arduino.

The main thing to understand with Arduino programming is the introduction of the General Purpose Input/Output pins. These pins allow you to send voltages out or receive voltages, meaning you can set a pin as power (output) or you can set a pin as ground (input). This allows you to control any number of circuits, which is why a lot of people start out today working with Arduino boards. If you're looking for a good place to start, try using an LED. You don't even need a breadboard to do this as Arduino includes a controllable LED in nearly all of their boards, and they even include an [example blink sketch](https://docs.arduino.cc/built-in-examples/basics/Blink/).

Lastly, expect to feel a little overwhelmed if you're working with Arduino's for the first time. A lot of Computer Scientists and Computer Engineers may not understand the electrical principles and a lot of Electrical Engineers may not understand the programming principles. If you don't understand a certain principle, ask questions. All of this project is looking to provide a way to introduce people to embedded systems and to show people how multiple disciplines can work together. You should be able to provide your knowledge to someone who doesn't understand a certain principle and they should be able to provide you knowledge with a different principle.

---

## Next steps

- [Sensor to trigger MIDI note on](https://github.com/BoffinFactory/PianoStaircase/issues/13)
- [Test and Document `qjeckctl` and `fluidsynth`](https://github.com/BoffinFactory/PianoStaircase/issues/9)
- [Time of Flight sensor demo](https://github.com/BoffinFactory/PianoStaircase/issues/2)
- [Ultrasonic sensor demo](https://github.com/BoffinFactory/PianoStaircase/issues/3)
- [Line break sensor demo](https://github.com/BoffinFactory/PianoStaircase/issues/4)

