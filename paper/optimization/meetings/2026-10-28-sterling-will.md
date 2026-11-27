# Meeting on the optimization manuscript, 2026-10-28 (Sterling and Will)

This is a transcript of Sterling's phone recording "Oct 28 at 3-09 PM Will - powder manuscript.m4a" (49 min 24 s, about 15:09–15:59 MDT). It was a working meeting between Sterling Baird and Will Mulberry on the optimization paper (#179, PR #184). During the meeting Sterling ran the Claude session in [`../tms-2027/session-2026-10-28.md`](../tms-2027/session-2026-10-28.md), which revised the TMS 2027 abstract, and posted the request that became PR #190. The audio is not in the repo.

**How it was made.**

- **First pass:** Whisper large-v3 (faster-whisper 1.2.1, int8 on CPU, beam size 5, VAD filter, English) transcribed the whole recording. Its uncorrected output is in [`2026-10-28-sterling-will.whisper.txt`](2026-10-28-sterling-will.whisper.txt).
- **Second pass:** two quiet passages (00:00–02:45 and 21:40–23:12) were decoded again without the VAD filter. This recovered speech that the first pass had garbled or replaced with hallucinated text; that output is at the end of the same file.
- **Correction:** Claude then corrected the text for intent and context:
  - Misheard terms were fixed against the draft, `OUTLINE.md` and the TMS README. Examples: "envelope repos" → angle of repose, "Hall Carnival" → Hall/Carney, "package of lights" → LIGGGHTS, "shear after flow" → τ_afterflow, "clock pings" → Claude pings, "Earth atmosphere" and "an urge" → inert, "circuit models" → surrogate models.
  - Filler words, false starts and most one-word acknowledgements were removed, and broken sentences were joined.
  - Square brackets mark words added for clarity. Italic brackets describe what was happening.
- **Speaker labels:** these come from the content, with per-segment voice clustering as a hint. Automatic two-speaker diarization (sherpa-onnx with pyannote segmentation 3.0 and WeSpeaker ResNet34) put about 92 % of the speech in one cluster, so it could not be used. In quick exchanges a label may be wrong.
- **Timestamps:** mm:ss from the start of the recording, marking where a turn starts.

## Main points

1. **What "physics-based property inference" means.** Sterling's example was moisture uptake (hygroscopicity). Give the simulation a parameter tied to the property, find the value that makes the simulated dosing match the measured dosing, then check that value against the standard test. The doser's data would then serve as a cheap proxy for the higher-fidelity ASTM tests. It works in both directions:
   - Dosing characterizes an unknown powder. This matters for the lab's own atomized alloys.
   - Known properties speed up calibration of a known powder. Will's version: powders that flow alike in a quick first test can shrink the BO search space.
2. **Tests the lab could run itself:**
   - Angle of repose, possibly from a camera watching the pile the doser makes, dosing into a glass vial.
   - Bulk and tapped density, in a vertical vessel without a screw, e.g. a thin-walled SLA part.
   - Hall/Carney flow, with a bought funnel set rather than the doser.
   - Moisture: dose before and after the powder sits in humid air. This is harder to control and needs a humidity gauge.
   - PSD from SEM images, or by laser diffraction.

   The shear cell needs an outside lab that has one.
3. **Objectives:**
   - Drop repeatability as an optimization objective, and report it afterwards from repeat doses.
   - Keep accessible dose range, since the best settings depend on the target dose. Sterling recalled that Sam's 13-powder data used 50, 200 and 1,000 mg targets.
   - Dose range matters more to people using the doser than to readers interested in powder properties. Will noted the two sides of the work: research for the paper, and an open-source tool people can use.
4. **Inert atmosphere: not at this stage.** Stay in air, inside a dehumidified enclosure. Some tests might be possible in Phillip's glove box at the University of Utah. Other groups' glove boxes are hard to get into because of the contamination risk.
5. **Lean into metals:** 630 bronze, Al 4047, Al 6063 and custom alloys. The symposium and the additive-manufacturing audience care most about these.
6. **Spreadability:** the lab can run its own blade-spread tests with the CubXL or a 3D printer with a wiper attachment, without a laser powder bed fusion setup. Will asked how the spreadability claim in the abstract would be validated, and this was the answer.
7. **Outreach:** get on calls with the symposium people. Sterling called that a "10× multiplier" compared with reading the manuscript and pinging Claude. Also contact heavy users or developers of LIGGGHTS, start sending emails, and possibly open a pull request for the outreach.
8. **Figures:** start with an overview figure, sketched in the meeting.
   - It links the cheap doser measurements (feed factor, tapping, angle of repose) to the standard tests (Hall flow, shear cell, PSD, moisture) as a relational matrix.
   - Surrogate models and physics-based simulations find the correlations. Context such as composition and powder history are extra inputs.
   - Will is to give Claude a photo of the sketch. The other figures wait for another meeting. The photo is in [`2026-10-28-whiteboard.jpg`](2026-10-28-whiteboard.jpg), and [`../figures/make_overview_relations.py`](../figures/make_overview_relations.py) draws the figure from it.
9. **Side request:** 3D animations of the property tests, with approximate costs (requested at 14:21, now PR #190).

## Transcript

### Opening, and what "physics-based property inference" means

**[00:03] Will:** …issue #124, which is where we first defined the optimization. I've been talking with Claude about which parameters we should optimize, and what we can just do manually.

**Sterling:** That makes sense.

**[00:20] Sterling:** …and go through our thing here. What's your schedule like?

**Will:** *[unclear]* 3:30… I'm free until four.

**Sterling:** Okay.

*[00:41–02:02: little speech while Sterling starts a Claude session on PR #184; see [`../tms-2027/session-2026-10-28.md`](../tms-2027/session-2026-10-28.md).]*

**[02:02] Sterling:** So I'm going to pull up the TMS title and abstract, and we'll start there, to ground us. That should pull it up. And right here I've got the outline Claude has put together: the different tasks for this paper, or what it thinks they should be. I guess it's got it right there, from `OUTLINE.md`.

**[02:39] Sterling** *(reading)*: "Auger-Based Powder Dosing as a Mechanistic Probe of Powder Flow Behavior: Multi-Task Bayesian Calibration and Physics-Based Property Inference." How do you feel about the title?

**[02:56] Will:** I understand the part about auger-based powder dosing as a probe of powder flow behavior, and the multi-task Bayesian calibration. I just don't really know what the physics-based property inference is.

**[03:14] Sterling:** Physics-based property inference (and we could rephrase it) essentially says we'll run simulations with the data we've collected, to help us infer what the properties would be if we ran the powder on big test equipment: all these standard powder properties.

**[03:41] Will:** Sorry, can you…

**Sterling:** Yeah, let's see.

**[03:51] Will:** So is it to inform how future powders behave?

**[03:56] Sterling:** What were some of the powder properties it talked about? I just need one. Does one come to mind?

**Will:** I had them listed out. One example would be hygro…

**[04:17] Sterling:** Okay, here we go. So we've got bulk density…

**Will:** Yeah, all of these.

**[04:24] Sterling:** Let's go with Hall flow. For Hall flow, you can… No, actually, let's talk about moisture for a second: hygroscopic powders. Say that with the powder doser you run a test in a semi-humid environment. You dose the powder before it has had a chance to take up moisture, and then you dose it again afterwards. You wouldn't necessarily have to run an official powder moisture-sensitivity test, like what it describes here.

**[05:25] Will:** Where you basically get it to take up some water, then put it in an oven to dry it…

**Sterling:** …and then you weigh it again. Not that that's super difficult. But say we took our auger, got the data, and ran a simulation: the particles go in, and there's some physics-based interaction with the moisture, the moisture affecting the powder. And we get the same moisture property out as if we had done the full oven-drying cycle…

**Will:** Oh, okay.

**[06:06] Sterling:** …by using our experimental data and a physics-based simulation that says, well, if the hygro… hygroscop… ah, man. It's going to come up.

*[06:18–06:52: they play a pronunciation clip of "hygroscopicity" and repeat it a few times.]*

**[06:52] Sterling:** So, that thing: hygroscopicity. Where was I going with that? In the physics-based simulation, say there's a parameter that's tied to hygroscopicity. We have our experimental results. We can ask: what value of that parameter makes the simulation match the experimental results we're getting with the auger? And does that value match what we would get if we had run the other, more complicated test? Does that make sense for the physics-based inference?

**[07:25] Will:** Yes. So you're saying we wouldn't necessarily have to measure the hygroscopicity physically?

**Sterling:** Mm-hmm. Yeah.

**[07:34] Sterling:** Maybe scroll down a little bit. So, shear… I guess another way to phrase it: just by knowing a few things about the powder we put in, could we basically say, "run a bunch of experiments on the auger," and autonomously predict what all these values would be if we had run the official ASTM measurements for all of them?

**[08:12] Will:** Oh, okay. I see.

**Sterling:** Does that make sense? So these would be proxy measurements for these higher-fidelity tests.

**[08:27] Will:** Okay. I think I'm understanding you now. I'm sorry.

**Sterling:** No, no, it's okay. I've been doing inference, Bayesian methods and other stuff for a few years.

**[08:40] Will:** So we're hoping to make a physics simulation…

**Sterling:** Yeah. And I don't know exactly what all of those [simulation parameters] are; that's one of the less defined parts.

**[08:51] Will:** …and we're hoping to make it accurate enough that if we put a new powder in, we could get the results and infer what different qualities are in the powder.

**Sterling:** Mm-hmm. Yeah.

**[09:09] Will:** As I've been drafting it, especially while setting up the Bayesian optimization campaign, it [Claude] talks a lot about how, if powders have similar values for any of these properties, that can reduce the number of iterations of the Bayesian optimization.

**Sterling:** Yeah, that makes sense.

**[09:33] Will:** So if you had a powder and you knew some of these values…

**Sterling:** …you could use that as a starting point for your dosing, right?

**Will:** Yes.

**[09:41] Sterling:** I like that it goes both ways. You could use the dosing to learn about an unknown powder, which is very relevant to us, with discovering new alloys and running our own atomization. So we could figure things out about our unknown powders, or we could take a known powder and quickly get the right auger parameters for fast, accurate dosing.

**[10:05] Will:** Yeah, that's what it's been talking about. Of course, I don't know how to implement that yet.

### Which property tests the lab could run itself

**[10:14] Will:** Looking at the properties (I had it find standard values for a lot of these), one of the biggest predictors of whether a powder flows well or not is the angle of repose, which seems like a pretty simple one: the slope the pile reaches before it avalanches.

**Sterling:** Yeah. Which is pretty interesting. So a steeper angle means it's harder to flow?

**Will:** Exactly.

**Sterling:** Gotcha.

**[10:48] Will:** Which is interesting too, because we can get that with the doser as well.

**Sterling:** Yes, true, you're right. We could literally measure the angle of repose with the right camera, as long as it's dosing into a glass vial or something like that. That's a good point; I didn't think about that.

**[11:10] Sterling:** I don't think that works for any of these other ones…

**Will** *(reading)*: "How much the powder compacts when tapped."

**[11:23] Sterling:** That one is also technically something we could do. Actually, we can do bulk and tapped density. We could make a different vessel that doesn't have a screw in it…

**Will:** …and hold it vertically…

**Sterling:** Yeah. And we could use the SLA auger.

**Will:** And we could make it really thin-walled. So I guess we could run our own tests.

**[12:00] Sterling:** And this one is just running powder through a funnel.

**Will:** Which one?

**Sterling:** Hall/Carney flow.

**Will:** Oh, okay.

**[12:13] Sterling** *(reading)*: "How many seconds does it take for 50 g to run through a standard funnel?" It's additive manufacturing's default.

**Will:** Okay. So you buy these special funnels.

**[12:34] Sterling:** Yeah. For that one it does sound like you just buy the funnel set and put 50 g in or so. I don't think we'd try to force the powder doser to do that.

**Will:** Yeah, for sure.

**[12:50] Sterling:** But I'd imagine all the data we've collected on how much powder gets dosed per revolution will be correlated with Hall flow. I'd expect those two to correlate.

**Will:** That's true. It's been calling that the "feed factor": the mass dispensed per revolution.

**[13:29] Sterling:** And that actually makes things complicated, because it isn't a standard property of a powder.

**Will:** It's probably a function of other things, like moisture. And how full the auger is seems to have a big impact on the feed factor.

**Sterling:** Absolutely. There's a lot that goes into it.

**[13:53] Sterling:** Can you scroll down a little to the shear [cell]? Okay: "a measure of cohesion: a shear cell, or a Schulze ring shear tester."

### Side request to Claude: 3D animations of the tests (became PR #190)

**[14:07] Sterling:** I'm going to do something real quick. This is #179, is that right?

**Will:** #184.

**Sterling:** Oh, #184. Okay.

*[14:21–16:00: Sterling types the request for animated 3D visualizations of the ASTM and other powder tests, with approximate costs, which was posted on PR #184 at 21:25 UTC and became PR #190.]*

**[16:03] Will:** Has it been listening to "one sentence"?

**Sterling:** Hilarious. It seems to listen to me, but it doesn't always listen to the other lab members.

**Will:** That's funny.

**Sterling:** I'm like, this is a teacher's-pet thing going on.

**[16:19] Will:** I saw one time where you told it two sentences, and it did two sentences, but each sentence had about five sentences in it.

**[16:29] Sterling:** Sometimes I'll say "max 300 characters", and that one it can't get around. But I saw somebody else's where they didn't use the same wording as me ("max two sentences"); they had some other wording, and it completely ignored it and gave a regular response.

**[16:56] Sterling:** Okay, I think this will help with visualizing what some of those other tests are like. Is it making sense? Here we've got this auger, and we do a bunch of things with it. We have all these properties that can be measured in all sorts of different ways, and we can go back and forth between them.

**Will:** Yes.

**[17:25] Will:** I'll probably have to ask again later for clarification on what direction we're going with this. And this might be a broad question, but where should I start?

**[17:39] Sterling:** This is a good transition. Let's read the abstract. Is that okay?

**Will:** Yeah.

### Reading the submitted TMS abstract

**[17:48] Will** *(reading)*: "Dispensed mass from an auger-based powder doser depends on actuator settings and powder properties, so every calibration curve doubles as a compact probe of cohesion, friction, and packing behavior."

**[18:00] Sterling:** I feel like it might need a… *[trails off]*

**[18:17] Will** *(reading)*: "We frame calibration of an open-source doser as AI-driven, multi-objective, multi-task Bayesian optimization…"

**[18:34] Will:** Oh…

**Sterling:** No, that was fine. It just sounds weird.

**[18:38] Will** *(reading)*: "…with objectives of dose accuracy, repeatability, dispensing time, and accessible dose range. Each powder is a related task—primarily alloy precursors, in elemental or master-alloy form depending on handling constraints and hazards, dosed under inert atmosphere, alongside feedstocks such as AlSi10Mg and stainless steel—and multi-task models share information across powders to cut per-powder calibration effort. Alongside gravimetric parameter sweeps, we are exploring discrete element modeling…"

**[19:22] Sterling:** That's DEM. That'll get used a lot, I think.

**[19:27] Will** *(reading)*: "…with cohesive-frictional contact laws…"

**Sterling:** That's the physics-based simulation part.

**[19:33] Will** *(reading)*: "…and measured particle-size distributions, enabling inference of effective cohesion and friction from dosing data, to be checked against shear-cell and Hall-flow measurements."

**[19:42] Sterling:** And that's where I think it would be received relatively well by others: "Oh, okay, you ran the same powder through these as a ground truth," as validation for it. And vice versa: if somebody measures these and knows the values, could we show that it helps speed up our calibration?

**Will:** Yes. Okay.

**[20:14] Will** *(reading)*: "Linking dosing response to these properties may anticipate downstream behavior such as spreadability and packing uniformity."

**[20:27] Sterling:** On one hand, the abstract got accepted, so obviously whoever read it thought, "sweet."

*[20:35–21:09: little speech while Claude answers which symposium the abstract is in.]*

**[21:09] Sterling** *(reading Claude's reply)*: Oh, yeah: "Powder Materials Processing and Fundamental Understanding."

### Talk to the symposium organizers

**[21:20] Sterling:** It would probably be worth reaching out to some of these people as well and getting on calls with them. Of anything you could spend your time on, getting on calls with this list of people would be, I'd say, a 10× multiplier. I could spend 30 minutes reading through the manuscript and doing Claude pings, compared with these calls. So I think it would be worth it: "contact them before the meeting".

*[22:00–22:30: little speech.]*

**[22:30] Will:** I guess that last part, where it talks about downstream behavior, spreadability and packing uniformity: are we doing things to validate that?

**[22:58] Sterling:** That's a good point, and it could be nice too, because spreadability is very important for laser powder bed fusion: you literally have a wiper spreading the powder over a bed, so poor spreadability means you didn't get your layer right.

**[23:19] Will:** Okay, so it's saying that, based on how it doses, we could maybe see how well it would spread.

**[23:26] Sterling:** Yeah. And I think it'd be worth trying some of our own experiments on spreadability. I think we could give you something like that.

### Going through `OUTLINE.md`: what is in scope

**[24:35] Sterling:** At this point I think it might be worth thinking through the figures. Actually, maybe go back to your outline, the `OUTLINE.md`. What would you say?

**[25:16] Sterling:** Sorry, you were saying… okay, the figure plan.

**[25:40] Will:** So basically it's saying we have the one campaign, on one powder. Of the objectives, time and error were optimized, and repeatability was measured after the fact.

**Sterling:** Yeah, that's just validating it, doing it a bunch of times.

**[26:05] Will:** And the dose range means that instead of only 0.5 g, some people might want 0.2 g and others 1 g, so depending on the target dose, that one gets complicated. Especially the lower bound. I think the upper bound would probably be fine, because it does the same thing all the way up until it gets close.

**Sterling:** Yeah. Except maybe for the time.

**Will:** What was that?

**[26:37] Sterling:** You want to really speed things up at the beginning, but not overshoot. Well, I don't know.

**[26:45] Will:** But it's easier, I'd say, to do 1 g than to say "I want 0.05 g".

**Sterling:** Yeah, for sure.

**[26:52] Will:** That was another thing I wanted to check: are these all things you want me to work on? Is anything out of scope?

**[27:03] Sterling:** Let's go one by one.

**[27:08] Sterling:** I do think we could leave repeatability out [as an objective] and just do it ad hoc, retroactively.

**Will:** Yeah. And this is repeatable.

**[27:26] Sterling:** I think we do need to bring in the dose range, in terms of somebody looking to quickly get their own calibration parameters. The parameters we use are probably going to be different depending on how much we're trying to dose. Does that make sense?

**[27:53] Will:** I forget how many parameters we're optimizing. Six or something?

**Sterling:** Eight, I think.

**Will:** Eight. Okay.

**[28:01] Sterling:** If we're only dosing 0.1 g, we would take some of those parameters and scale them down compared with dosing 1 g.

**Will:** Right.

**[28:12] Sterling:** So there's this question of the optimal parameters as a function of the powder type (what the powder is), how full the auger is, things like that, and what we're actually trying to dispense: the amount.

**Will:** Our target dose. That makes sense.

**[28:44] Sterling:** I think the dose range is in the data Sam was focusing on collecting, and maybe you collected some of that data too. I forget.

**[29:02] Will:** The big campaign of tests on all the different powders, the 13 powders? I thought you guys were doing that. And by "data", you mean what the dosing looked like? Like "run all these tests on this powder, without any optimization"?

**Sterling:** It was just a bunch of tests to check.

**Will:** I think you guys had split that off.

**[29:28] Sterling:** I think that might have been Sam. Yeah, that's right. In the data he collected, I think he had 50, 200 and 1,000 mg target doses.

**Will:** Oh, okay. So it would run with each of those three as targets.

**[29:53] Sterling:** So for accessible dose range, it would be something like that.

**[30:05] Will:** That's more on the optimization side, and maybe ties in less with the powder properties.

**[30:11] Sterling:** I'm not really sure it's something people would care about from the powder-property side of things. It's definitely for somebody who has the doser, wants to dispense some amount, and doesn't want to spend as much time calibrating it.

**[30:34] Will:** That's another thing I've been thinking about: there are two sides to this. One is the research for the paper, and the other is making this open-source and usable.

**Sterling:** Yeah. Okay.

**[30:49] Will** *(reading the status table)*: "Every calibration curve is a probe of cohesion, friction, packing… 24-fold delivery range, no-flow powders, Si size pair; delivery ranks like literature angle of repose; per-powder τ_afterflow, tap quantum, speed exponent." So this is what I was saying earlier: its ability to dose seems to be very correlated with the angle of repose.

**[31:22] Sterling:** Okay, gotcha. Cool, that's cool.

**[31:35] Will** *(reading)*: "Measured properties of the same lots; batch-to-batch resolution."

**[31:40] Sterling:** For that one, I think we run the official test: actually do an angle of repose test.

**Will:** Oh, okay.

**[31:52] Will** *(reading)*: "Each powder is a related task; multi-task models cut calibration effort… salt settings carried over to AlSi10Mg."

**[32:05] Sterling:** I guess that's saying the salt settings were fine for another material, but they're certainly not going to be the optimal ones.

**[32:21] Will:** Yeah. And salt and the AlSi10Mg had similar flow behavior; both flowed very easily.

**Sterling:** Yes. Okay.

**[32:32] Will:** So maybe that's what it's getting at: if powders have similar properties, or even just flow similarly in a very initial test, we can shrink the search space for the new powder.

**Sterling:** Yeah. Okay.

### Inert atmosphere and glove boxes

**[32:53] Will** *(reading)*: "Alloy precursors, elemental or master alloy, under inert atmosphere; AlSi10Mg and stainless steel."

**[33:02] Sterling:** So we've done those two doses in air, not with steel. And then we did those… you guys had them at the University of Utah?

**Will:** Oh yeah, that was…

**[33:21] Sterling:** So that's what this is referring to: salt and then those other two things [norbornene and AIBN].

**Will:** That's right in there…

**Sterling:** …with it shaking itself apart.

**[33:34] Sterling:** In terms of a glove box, we really don't have a go-to here. I think Phillip would be down to let us use that glove box back at the U for testing. Maybe somebody would let us bring something into one of their glove boxes, but people are very cautious, and for good reason, about what they let into a glove box. They're often doing things that require a high level of control of oxygen, moisture and purity. So it's like, "Oh, well, you just introduced something to the glove box, and now it has contaminated all of it: you've got this powder that's just flowing in the open."

**[34:17] Sterling:** But it sounds like we could still do some things with that at the U. I don't think it's reasonable to say we'll do everything under inert atmosphere at this stage. I don't think we're going to get there. I think we'll just stick with air, but we can do it in the enclosure, where it's hopefully drier than other places. So instead of inert, it'll just be a dehumidified enclosure.

**[34:53] Will:** So that one is basically saying: do the optimization campaign with the metals.

**Sterling:** Okay. Yeah, that's right.

**[35:00] Sterling:** I think the more we lean into metals, the more people from this symposium, and from additive manufacturing in general, are going to care. They're going to care about the metals: the 630 bronze, the Al 4047, Al 6063, custom alloys. That's up to you.

**Will:** Yes.

### DEM, Hall flow, shear cell and spreadability

**[35:23] Will** *(reading)*: "Discrete element modeling…"

**Sterling:** I think that's what DEM stands for.

**[35:26] Will** *(reading)*: "…with cohesive-frictional contacts and measured particle-size distributions… LIGGGHTS twin…"

**[35:33] Sterling:** That's just a ridiculous name for a package: LIGGGHTS.

**Will:** What is that?

**[35:44] Sterling:** It's a package for running certain kinds of simulations. It seems like it found a good package. I think I told it to run some things with it, which is why it says "forward model done".

**[36:08] Will:** Okay. So this is the simulation.

**Sterling:** Yeah, that's right. I could probably pull it up another time.

**[36:17] Will** *(reading)*: "Checked against shear-cell and Hall-flow measurements."

**[36:23] Sterling:** We can probably run our own Hall flow just fine. We'll need to find somebody with the shear-cell equipment. I don't know how complicated that's going to be.

**[36:37] Will** *(reading)*: "May anticipate spreadability and packing uniformity… blade-spread single layers on 3–4 deliberately varied batches."

**[36:50] Sterling:** So that's one where we decide whether we use something like the CubXL, or one of the 3D printers with a wiper attachment, and run some of our own spreadability tests.

**Will:** Oh, okay.

**[37:08] Sterling:** I think we could get creative and run some of our own tests, without having to go to some fancy laser powder bed fusion spreadability setup. I think we can get a quick version of it.

**[37:30] Will:** I think that's making more sense to me. This one especially is one I'd want to consult people on a lot, like you said: talking to the people from the symposium.

**Sterling:** Yeah, I agree. I think that'd be really good. You could even reach out to the heavy users or developers of that particular package [LIGGGHTS]. And that's a good symposium for finding people who really care about powder properties. Reach out. We can probably get another pull request tied to that.

**[38:21] Will:** Should we reach out by email?

**Sterling:** Okay. Let's start sending some.

### Figure brainstorm

**[38:27] Will:** If we go down a little bit…

**[38:30] Sterling:** What did you say? I think this is a good point to brainstorm some figures. This was me brainstorming different figures with Sam.

**Will:** Oh, okay.

*[38:55–39:50: little speech; they look at the figure sketches.]*

**[39:50] Will:** I think an overview figure is going to be pretty important here.

**[39:54] Sterling:** Yeah, just to help the audience (the readers, or the audience at the symposium) make the connection. Like: here's our powder doser, and maybe we have a couple of things here, like a transparent…

*[40:10–40:41: sketching, little speech.]*

**[40:41] Sterling:** …the ghost… ghost dose *[unclear]*. That one I think we can get.

**[41:10] Sterling:** We can do Hall flow, AlSi10Mg, different… I don't know. Like we were talking about, a lot of things factor into how that's actually going to behave.

**[41:28] Sterling:** So we have this as, I guess, different angles.

**[41:43] Will:** Oh yeah, so tapping here, so we can close that off.

**[41:48] Sterling:** And then, that's right, angle of repose.

**[41:56] Will:** In that case, would we want it at a 90° angle? Or, I guess, if we do a really low angle… Either way, we're going to do something where…

**Sterling:** You mean for testing the angle of repose?

**Will:** Yeah, is that what we have?

*[42:18–42:58: little speech.]*

**[42:58] Sterling:** Oh, okay, I see. What were some of the other ones we talked about, where we can measure it directly versus [infer it]…

**[43:21] Will:** Well, Claude told us we can test the moisture in-house. I don't know how we would, but…

**[43:29] Sterling:** Oh, for the moisture, we can basically just let the powder sit out and do runs before and after it's been exposed to humid air. Now, that one's a little harder to control.

**[43:55] Will:** Yeah. It's like, do you stick it next to a humidifier, spread the powder out, take a little spray bottle…? Do you need some sort of gauge reading the humidity?

**Sterling:** Yeah.

**[44:10] Sterling:** Let's see: bulk density, angle of repose. There's the particle-size distribution, which would be pretty interesting, because we can get that through a couple of methods. One would be… let's see, PSD… we could do that from SEM images.

**[44:38] Will:** Oh, okay, yeah. That's what Ronnie *[name as heard]* does a lot of, right?

**Sterling:** Yeah, that's right. There are also other methods, like laser diffraction, and…

*[44:52–45:14: little speech while they sketch.]*

**[45:14] Sterling:** Is that starting to make sense? Could we use all this stuff to actually predict what the particle-size distribution is?

**Will:** Oh, okay, I see.

**[45:25] Sterling:** Imagine we got this without having to take it to very expensive equipment. But we've got the shear cell, which… let's see, this is…

**[45:44] Sterling:** Oh, okay, yeah. Feed… was that the feed factor?

**Will:** Yeah, yeah.

**Sterling:** Feed factor. And then…

**Will:** And then the Hall…

*[46:00–46:24: little speech while they sketch.]*

**[46:24] Sterling:** Hygroscopicity… it's Hall flow, right? What do they call that?

**[46:39] Will:** Oh, sorry, what time is it?

**Sterling:** I don't know… oh, 3:56. Okay. So let me just… Hall.

**[46:48] Will:** We've got the shear [cell]. I don't know what that looks like at all.

**Sterling:** Yeah, it's like a normal… *[unclear]*

*[47:01–47:17: sketching.]*

**[47:17] Will:** So you're seeing what… and for the overview figure, it's like: we can do these very cheaply.

**Sterling:** Yeah. Some of these are cheap, some are more expensive. Can we get a kind of relational matrix of…

**Will:** Yeah.

**Sterling:** Great.

**[47:48] Will:** And this would be the objective of the simulation? The simulations and the machine learning, like the Bayesian optimization models…

**[47:58] Sterling:** The surrogate models and the physics-based simulations would help us find correlations between these.

**[48:06] Will:** So it's like: if we know all of this, could that help us know what this is?

**[48:10] Sterling:** And there are a lot of contextual things too. This is all about the actual experiments, but there are things we know, like state and history: what's the composition, what do we know about the powder already? Could we use what we know about it, plus these simple, easy-to-run tests, to help predict some of the things people often measure and care about?

**Will:** Okay. Yeah.

### Wrap-up

**[48:52] Sterling:** That's just one figure. Maybe another time we can go through the rest of the figures we want to look at. I don't know if you have time, but if you could throw that picture at Claude, it could probably make a pretty decent [version of] this one.

**Will:** Yeah, I can do that.

**Sterling:** Cool.

**[49:14] Will:** I might not… well, actually, I'll have time again later.

**Sterling:** Okay, very good. That's fine.

**[49:22] Will:** I'm sure this will just take a while for me to… *[recording ends]*
