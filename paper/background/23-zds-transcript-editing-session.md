# Zoo Design Studio - Editing Session Transcript

**Video:** [Testing Generative AI in Zoo CAD software to design a simple part](https://youtu.be/DwFI1eQ_3bI?si=OgWHD90ix_3XAwnf)  
**Participants:** @williamulbz, @sgbaird  
**Source:** Auto-generated YouTube transcript, edited for readability

---

## Setup & Initial Context

**[0:00–0:45](https://youtu.be/DwFI1eQ_3bI?si=OgWHD90ix_3XAwnf&t=0s)**

We're going to use number four. I only have the STL for it, but hopefully that will be enough.

It says non-KCL files aren't editable, but I guess we don't need it to edit it anyway. Hopefully it can play with it. We'll see.

---

## Auger Part Selection & File Import

**[0:60–2:32](https://youtu.be/DwFI1eQ_3bI?si=OgWHD90ix_3XAwnf&t=60s)**

The STL for the auger should be in the repository. I can only find the test versions right now, which are just the shorter file. But it's in the repository.

It's type four. Yeah, and there was a mismatch on one of these—I think two and one were mixed up.

---

## Gripper Design Discussion

**[3:54–4:32](https://youtu.be/DwFI1eQ_3bI?si=OgWHD90ix_3XAwnf&t=234s)**

So we're creating a gripper. When it comes down on the rack thing, it grabs it and holds it—the gripper slash brackets. That was the same thing I was doing.

We need to think about what else we need. You look at like the actual thing that stores it, how it's being held.

---

## AI Reasoning Process & Self-Validation

**[15:04–20:34](https://youtu.be/DwFI1eQ_3bI?si=OgWHD90ix_3XAwnf&t=904s)**

It's like nerve-racking, but it's alive. I just told it something that can hold the auger. For a minute it was thinking of a U-shaped saddle and then it was like, "No, let's do a V-shaped saddle instead." It's still working on it.

It's cool that it's kind of checking itself. It just added a feature and resets. 

I feel like for a lot of this stuff, because it's such high-level design, we have to be thinking about how it's going to fit onto the rack thing and how that's going to work. It's hard to explain all of that in a prompt.

I can tell it like this, and I already enjoy it more than Copilot. But I think if we treated it the same way we did Copilot—very intermittently where we make our sketches and our ideas—we'd like it even more.

It does already seem better. It should hold it. Oh, is this to keep it from sliding? Maybe.

I like that it gives all its thinking. Yeah, and it got the dimensions right from the STL, so that's good.

---

## Feature Tree & KCL Synchronization

**[20:28–26:47](https://youtu.be/DwFI1eQ_3bI?si=OgWHD90ix_3XAwnf&t=1228s)**

It's done. Wow. Now I have access to all the features. So we got the feature tree. That's worth it, just right there. That's pretty cool.

So I can see what each extrude does. When you do something in the UI, does that change the KCL code?

Yes, it seems to. The rendered version and the AI's coded version are technically the same thing. If we ask the AI to change something, it changes the code, which changes the model. If we change something on the model, it also changes the code so the AI can see it.

It constantly updates the code. The biggest challenge now is that it's not just about making stuff—it can make stuff, sure—but the constraint is that it can't hold all the things it needs to hold to actually do this. That's the biggest limitation.

---

## Editing & Parameter Constraints

**[56:01–57:06](https://youtu.be/DwFI1eQ_3bI?si=OgWHD90ix_3XAwnf&t=3361s)**

Have you tried editing anything by hand?

Watch this. I'll say I don't want this to be parametric. I just want it to be 70 mm.

It doesn't let me. It jumped back.

You can change it from the parameters section. Yes, you can, but every parameter is controlled by like three other parameters. And then even more, you know.

Let me try to start a sketch. You can't make a new sketch. Can't find the source code for this. We can't actually edit it. Yeah, I still think it's better though.

---

## Gripper Design Iteration & Assembly Concepts

**[27:00–33:35](https://youtu.be/DwFI1eQ_3bI?si=OgWHD90ix_3XAwnf&t=1620s)**

Now that it's showing me the iterative process, let's check if this works. It's a gripper—I don't know how it's supposed to work, but we'll see what it says.

One of the biggest downsides we've talked about is that we're holding so much in our heads as designers: it has to fit with this, and it has to do this and that kind of thing. It's really hard to tell that unless we're designing the whole system at the same time.

So it might be a great gripper, but it would never work without the right design context. For the purpose of this—to dispense powder—can we import the whole system? The scale is already there, and this is where the powder gets loaded.

Maybe a rudimentary simulation would be useful. It's not so we can test everything for real, but at least we can have an internal feedback loop. If it doesn't work in simulation, it definitely won't work in real life. That's useful.

---

## Model Validation & Constraints

**[33:57–34:51](https://youtu.be/DwFI1eQ_3bI?si=OgWHD90ix_3XAwnf&t=2037s)**

Oh, look. It can detect that it has floating bodies. It says these bodies have no overlap. It's fixing it because right now you can see when these parts are not connected, but it knows like, "Hey, this shouldn't be right."

That's great. That's already spatial reasoning—better than Copilot can do.

So funny—the first couple times I was like, "How many bodies are in this file?" I said one. No, no, no...

---

## Design Inference & Missing Context

**[30:31–31:51](https://youtu.be/DwFI1eQ_3bI?si=OgWHD90ix_3XAwnf&t=1831s)**

So there's an auger with a helix. That's important. But it assumed this because I didn't give it all the information. The more context I can give it, the better it would be. And that's where maybe giving it the entire assembly would help—saying, "You need to build something that can do this swap." Then it's hard when we're iterating on the design.

Should I give it this with new information? If we want to move past this design and have it interface with parts we don't actually have yet, how does this work? Yeah, I think pictures and screenshots, drawings, stuff like that would help.

---

## Component Analysis & Assembly Mating

**[36:27–37:59](https://youtu.be/DwFI1eQ_3bI?si=OgWHD90ix_3XAwnf&t=2187s)**

This is a fence. It uses motors—one here to turn everything and then another motor here with this rod to open and close the gate. But this rod is not connected to those at all. That's not bad though. It has guide rollers—these little things are not attached to anything, but that's a good idea to make sure it gets into just the right spot.

Well, I guess you could do that with just making the claw in the right shape.

The task you gave it was definitely more complicated. When it came back with its solution, it realized these need to be connected. It went through and fixed it. Did you tell it to change it? Yes, so now I'm going to see if I can edit these parameters.

It has like 29 parameters, 26 parameters... If I could just check these references and make sure those are real, then I think we're good to go on that one.

---

## Assembly Handling & Design Coordination

**[40:31–41:51](https://youtu.be/DwFI1eQ_3bI?si=OgWHD90ix_3XAwnf&t=2431s)**

I'm not sure what I want to give Zoo—like an assembly file where it's one body and it understands all the pieces, keeps them separate, and knows how they mate. That's interesting. Yeah, that's why we're playing around with it though.

---

## Model Recognition & Understanding

**[50:58–52:03](https://youtu.be/DwFI1eQ_3bI?si=OgWHD90ix_3XAwnf&t=3058s)**

I just gave it the full STEP file of the assembly. Hopefully it likes that. I'm seeing that it understands what I'm talking about more.

Yes, yes. It's hugely impressive. It recognizes where things are, what parts of things I'm talking about. And now I can refer to what it names things too. Yeah. I feel like the whole time we were using Copilot, this stuff would have been way easier. But now trying to carry things over from Copilot is getting tricky.

---

## Comparison & Feedback Cycle

**[52:01–53:26](https://youtu.be/DwFI1eQ_3bI?si=OgWHD90ix_3XAwnf&t=3121s)**

It's got me thinking about job security again. But that's a pretty good metric that this one didn't make you scared like Copilot did. Yeah, it's like with AI, there's fear and trust—all these different emotional elements. It doesn't respond quite the same way as Copilot, so I'm not sure what I can say. It's not as text-based. It's going to kick out a model and a little reply quickly. Well, the feedback cycle has been pretty long—15, 20 minutes, actually.

---

## Lazy AI & Explicit Instructions

**[52:51–54:01](https://youtu.be/DwFI1eQ_3bI?si=OgWHD90ix_3XAwnf&t=3171s)**

I did see something funny. I think it was you—you told it to stop being lazy. Oh yeah, it's got to have like "stop being lazy." When I know it's probably going to be lazy, sometimes I'll say don't be lazy. Because the times when it gets lazy, it's like, "Oh, for me to do what you're asking, I'm gonna have to download 400 megabytes of this project, install it, compile it." Instead of doing that...

---

## Manual Verification & AI Hallucination

**[58:16–59:57](https://youtu.be/DwFI1eQ_3bI?si=OgWHD90ix_3XAwnf&t=3496s)**

I have to tell it very specifically not to hallucinate. It's funny because I'm telling the AI agent to manually verify each link one by one. If it goes to 404, that's fine. I have to constantly tell it that it's okay for it to fail. It's okay for it to not answer.

It's an interesting dynamic when AI is engineered specifically to always give back a correct answer. I want a process where it can fail in the middle and we can move from there.

My dad has been using AI more, and he has one prompt that he always uses. It's some context about him, like "This is this kind of thing and never, ever, ever hallucinate a source." Right. Telling it not to hallucinate a source—hopefully it's gotten better with that.

It has. But it's funny that after he's told it that and given it that context, then everything is way more helpful because it has a little bit of context. It's just weird that it needs that. It's like, don't lie to me, and then it's like weird.

---

## Final Checks & Publication

**[62:06–62:09](https://youtu.be/DwFI1eQ_3bI?si=OgWHD90ix_3XAwnf&t=3726s)**

You want me to publish this now? Yeah, I think we're good to publish it.
