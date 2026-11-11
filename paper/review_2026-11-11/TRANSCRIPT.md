# Transcript: Sterling's review of the v2 figures and tables (PR #209)

Video: <https://youtu.be/jVrScVe-4QI> ("Powder doser manuscript review / feedback", unlisted,
uploaded 2026-11-11, 12:09). A screen recording of the
[PR #209 description at `113750b`](https://github.com/vertical-cloud-lab/powder-doser/pull/209),
scrolled from Fig. 1 to the tables, with the mouse pointing at what each remark is about. The
feedback is collected and acted on in [NOTES.md](NOTES.md).

**How this was made.** YouTube blocks the GitHub runner, so the audio and the 1850 × 1154 video
track were streamed through the lab Pi with a 2 MB/s cap. Nothing was written to the Pi's disk.
The audio was transcribed with faster-whisper `large-v3` (int8, CPU, word timestamps); the raw
output is in [TRANSCRIPT-whisper-raw.txt](TRANSCRIPT-whisper-raw.txt). Unclear phrases were
re-transcribed with `large-v3` (two temperatures), `large-v2` and `medium.en`
([tools/snippet_retranscriptions.txt](tools/snippet_retranscriptions.txt)). To see what "this"
and "here" meant, the cursor was tracked at 10 frames per second, and each sentence was drawn
over the screen with the cursor's path and the words spoken along it. Unclear moments were also
checked as burst screenshots at 2 to 4 frames per second ([tools/](tools/)).

Corrections are in square brackets. *Italic notes* say where the cursor was. Each timestamp links
to that moment in the video.

---

### Fig. 1 The doser

[`00:01`](https://youtu.be/jVrScVe-4QI?t=1) I like this overall.
*(Fig. 1 on screen.)*
[`00:04`](https://youtu.be/jVrScVe-4QI?t=4) These are a little lackluster.
*(Scribbles back and forth over panels (c), the auger section, and (d), the beaker photo.)*
[`00:06`](https://youtu.be/jVrScVe-4QI?t=6) That could probably be replaced with a mount [cam?], maybe.
*(Rests on the powder pile in (d), then points at the top-right corner of (d), then returns to
the powder. Whisper heard "mount cap" (large-v3, medium.en) or "round cap" (large-v2).)*
[`00:12`](https://youtu.be/jVrScVe-4QI?t=12) Actually, all of these need to have the caption.
[`00:15`](https://youtu.be/jVrScVe-4QI?t=15) It's really important that the caption gets shown in
tandem with this, not as embedded text, but for me to review.

### Fig. 2 AI agents and engineers

[`00:23`](https://youtu.be/jVrScVe-4QI?t=23) This one is looking pretty good right here.
*(Fig. 2a scrolls into view.)*
[`00:25`](https://youtu.be/jVrScVe-4QI?t=25) That is too small and not high res enough, and could
probably be vertically oriented.
*(Circles the "Whole module, one request" thumbnail.)*
[`00:32`](https://youtu.be/jVrScVe-4QI?t=32) The text over here should be left aligned.
*(Circles the "Powder excavator / Copilot / Opus 4.7" label, then runs along the row of labels.)*
[`00:39`](https://youtu.be/jVrScVe-4QI?t=39) Maybe a slight separation between Copilot and Opus 4.7
and such, just a slight distinguishing between those. Or you could use a lighter color to
indicate the model.
[`00:56`](https://youtu.be/jVrScVe-4QI?t=56) These arrows are sort of okay, but they should be
pointing to the actual, uh, frame. Notice that they're not actually attached to them.
*(Traces the lines from the dates up to the thumbnails, and the gap under the "Whole module"
frame.)*
[`01:11`](https://youtu.be/jVrScVe-4QI?t=71) And then it looks kind of weird to have them as just
straight arrows. It should probably go up, to the side, and back up, or something like that.
*(Draws it: straight up from a date, right along the row, then up into a frame.)*
[`01:23`](https://youtu.be/jVrScVe-4QI?t=83) And then for the caption for this one, it would
probably be worth pointing out some specifics, like… well, anyway, maybe we get the link to
certain places.
*(Scrolls between the Fig. 2 caption line and the timeline.)*
[`01:52`](https://youtu.be/jVrScVe-4QI?t=112) I'm not really sure why (a) and (b) are divided like
this here. I'll just assume… well, yeah, you should be showing both of them together. Also,
having (a) and (b) in the same figure makes this kind of a huge figure.
[`02:15`](https://youtu.be/jVrScVe-4QI?t=135) Maybe (b) could be its own figure, with tap collar up
top here, and then taking auger and bracket and putting that below, and then that could itself be
a three-part figure, more focused on… I think the point was, like, this being… well, I kind of
forgot what the point of this was. Oh yeah.
*(Over Fig. 2b: the tap-collar group "up top", the auger and bracket groups "below".)*

### Fig. 3 How a dose runs

[`02:49`](https://youtu.be/jVrScVe-4QI?t=169) This is sort of fine. This is weird right here, with
this little snippet there, I guess. I don't know, that's just kind of weird.
*(Circles the small phone screenshot, "Dispensing 8 g of Al 4047", between the chat cards and the
schematic.)*
[`03:03`](https://youtu.be/jVrScVe-4QI?t=183) This is fine, probably. (c) looks fine. [(b)] is just
kind of a confusing figure for me. I feel like that could be more straightforward, maybe just by
having it go linear, with a loop back in on itself.
*(Whisper's first pass heard "E"; all four re-transcriptions hear "B". The cursor is on the
feedback-loop schematic.)*

### Fig. 4 Using the doser

[`03:35`](https://youtu.be/jVrScVe-4QI?t=215) This looks good, yeah. Showing the cap, fitting
the… tap collar on, showing it over the cup.
[`03:49`](https://youtu.be/jVrScVe-4QI?t=229) (c) could probably use a callout for, like,
aluminum, what was that, 6063 [?], for that bar there; that's a… that's like a cup.
*(Points at the metal tube that runs from the paper funnel down into the glass beaker in (c).)*
[`04:01`](https://youtu.be/jVrScVe-4QI?t=241) Nice on this one. Um, and maybe Sam's gonna replace
that.
*(Over (d), the labelled augers.)*
[`04:07`](https://youtu.be/jVrScVe-4QI?t=247) (a), (b), (c), (d): all of this should be aligned.
It's weird for (d) to be lower, and then this top right… like, a little bit weird.
*(Runs along the panel letters; then circles the italic note "Label, and delivery per
revolution at 22.5°" above (d).)*
[`04:28`](https://youtu.be/jVrScVe-4QI?t=268) Yeah, you don't need to say it's a label; obviously
it is a label. And then "delivery per revolution at 22.5 degrees": probably you just put the
22.5 degrees in the caption, with a little asterisk or similar next to one of them that says
"per rev".
*(Points at "NaCl (table salt) 146 mg per rev.")*

### Fig. 5 Open-loop delivery

[`04:47`](https://youtu.be/jVrScVe-4QI?t=287) The open-loop delivery figure: yeah, that's fine on
the left.
[`04:55`](https://youtu.be/jVrScVe-4QI?t=295) (b), mass per solenoid tap. Okay, that's fine to have
it as a fine tap. It's fine to have this kind of showing the standard deviation of a particular
tap. That is important, especially in terms of predicting what's going to happen.
[`05:30`](https://youtu.be/jVrScVe-4QI?t=330) And then, yeah, mass delivered, that's good.
*(Panel (c).)*
[`05:33`](https://youtu.be/jVrScVe-4QI?t=333) What is confusing me is how the… well, first off,
you've got the x-axis here; you don't need to say log scale, obviously it's log scale. And then
the x-axis label is bleeding into the kind of bounding box for (b).
*(Underlines "(mg, log scale)" in (a), then outlines panel (b).)*
[`05:57`](https://youtu.be/jVrScVe-4QI?t=357) And then it's also not totally clear; yeah, the
legend is confusing to me, because… okay, yeah, obviously the blue and the orange are the legend
for (a), but that legend should probably be embedded in this kind of white space right here.
That would probably be a better place for the legend. That's not being used.
*(Circles the empty area of (a) to the right of CMC, white rice flour and sodium alginate, above
the grey "no measurable delivery" band.)*
[`06:25`](https://youtu.be/jVrScVe-4QI?t=385) And then this is pretty confusing: "Tap resolved",
"Tap within balance noise", and "Run failed screening". It's confusing because of the scale up
here, and I don't necessarily want to change this to log scale to make it obvious. So it kind
of makes me think, like, maybe just don't have these in here. I'm not even sure what the point
is here, "tap within balance noise"… I don't know, this is really confusing to me.

### Fig. 6 Closed-loop doses

[`07:09`](https://youtu.be/jVrScVe-4QI?t=429) Figure 6. Okay, first off, way too many dots
without clear separation between (a), (b) and (c); that makes it difficult to look at.
[`07:21`](https://youtu.be/jVrScVe-4QI?t=441) And then we're looking at 50 mg, 200 mg and 1 g
targets. It seems like there would actually be a way to show this all at once, but then we
couldn't necessarily do percent of target. Maybe, maybe if we had (a), (b) and (c) all
together… but instead we're showing… I don't know. Maybe this one would be better as…
actually, yeah, I don't really know how to deal with this.
[`08:19`](https://youtu.be/jVrScVe-4QI?t=499) Same kind of feedback with the legends; yeah, super
confusing. It's not clear what corresponds to (a), (b) or (c) (in this case it corresponds to
all of them), but do we really need to say "research-relevant, outside limit" when we already
have the green band that shows it's outside? Maybe, maybe not.
*(Points from the legend entry to an open square outside the green band in (b).)*
[`08:46`](https://youtu.be/jVrScVe-4QI?t=526) But either way, this one could really use some
refining, visually, in terms of what it actually conveys, like a message. First off, there
should be the caption that we can review in tandem with this: what the main takeaway is. That
should be the first sentence, or first or second sentence, a statement of what the takeaway
here is.
[`09:17`](https://youtu.be/jVrScVe-4QI?t=557) "14 of 30 within ±10%". Oh yeah, the text here
should be left aligned. Like, this two-line text should be left aligned.
*(The centred two-line panel titles.)*
[`09:30`](https://youtu.be/jVrScVe-4QI?t=570) And I'm realizing part of the confusion here is that
you've got symbols lined up right with (b), and so there's actually a little bit of overlap
between one of the symbols for (a) and the caption, or the legend, for (b) there.
*(The off-scale triangles at the right edge of (a) touch the "(b)" label.)*

### All figures

[`09:51`](https://youtu.be/jVrScVe-4QI?t=591) You know what, I think in general I'd actually much
prefer, like, part (a), (b), (c)… well, no, maybe not for this one. But it gets me thinking about
LaTeX subfigures. But that would be difficult for this one. But also, we don't even… we don't
need that. And this should be… there's, like, a much easier way to show this, probably by… well,
I don't know, never mind.
*(Scrolls from Fig. 6 up to Fig. 3.)*
[`10:28`](https://youtu.be/jVrScVe-4QI?t=628) On Figure 3, that's maybe kind of an exception, but
at least for, like, Figure 4 and Figure 5, also Figure 2, and what I described with Figure 2b,
also Figure 1: yeah, all of these can be LaTeX subfigures. This one's kind of the only exception,
and maybe it'll become a little bit clearer once this does get kind of fixed up.
*(Fig. 3 on screen.)*
[`11:14`](https://youtu.be/jVrScVe-4QI?t=674) Oh yeah, the arrows. You know, just in general: the
arrow doesn't have meaning here; it should just be a line, not an arrow. Let's start with that.
*(The leaders from the Fig. 3 keyframes down to the dose trace.)*

### Tables

[`11:29`](https://youtu.be/jVrScVe-4QI?t=689) For tables: okay, I actually wanted to see the actual
tables here, in Markdown. Yeah, so I guess that's the feedback: show me the actual tables.
*(The PR description lists the tables in a summary table instead.)*
[`11:53`](https://youtu.be/jVrScVe-4QI?t=713) [Tries to hide the PR description.] Oh no, I can't
hide this, can I? I can't hide it, but maybe I'll start hiding the other ones as we do additional
things, to make it just a little bit easier to find the latest version.
