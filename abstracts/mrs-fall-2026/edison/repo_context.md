# powder-doser repository context (issues and pull requests)
NOTE: The main branch is sparse; most development lives in issues and PR branches.

## ISSUES

### Issue #1 [OPEN]: Initial prototyping and design of mini excavator
https://github.com/vertical-cloud-lab/powder-excavator/blob/main/powder-excavator-sketch.jpg

We're thinking of using a pure mechanical approach that can be connected to a gantry system, which can be pushed up against a wall or similar to get the deep ladle/style to drop powder

### Issue #3 [OPEN]: Technical viability: dose control, powder adhesion, and mechanism design
Follows from #1. This issue works through the technical viability of the powder-excavator
  mechanism before prototyping begins. The design is a semicircular scoop (mm–cm scale, 3D                      
  printed) mounted on the Genmitsu 3018-PROVer V2 gantry. Pins on the flat sides of the scoop                   
  catch a ledge, pivoting the bucket to dump into a vial or onto a flat surface. Powder is                      
  micron-sized; target dose range is micrograms to milligrams.                                                  
                                                                                                                
  ## Challenge 1: Dose control                                                                                  
                                                                                                                
  Two approaches:                                                                                               
   
  **A. Dip depth control** — vary how deep the scoop enters the powder dish to control fill                     
  volume. Simple, fully mechanical, no extra hardware. Problem: micron powders don't fill
  predictably by volume. They compact, bridge, and channel, so the same dip depth gives                         
  different masses each time. Workable for rough milligram-scale doses but not microgram                        
  precision.                                                                                                    
                                                                                                                
  **B. Closed-loop gravimetric (recommended)** — place an analytical balance (0.1 mg resolution,                
  ~$100–500) under the deposition target. Dispense one scoop, weigh, dispense again if short,                   
  repeat until target mass is reached. This works regardless of fill variability and is the                     
  standard approach in pharmaceutical powder dispensing. Requires integrating the balance                       
  readout with gantry control (serial or USB), but achieves true microgram-milligram precision.                 
                                                                                                                
  Recommendation: closed-loop gravimetric with small scoops as the dispensing unit. Dip depth                   
  can still be used to tune scoop size roughly.                                                                 
                                                                                                                
  ## Challenge 2: Powder adhesion and dump completeness
                                                                                                                
  Micron powders are dominated by surface forces (electrostatic, van der Waals), not gravity.                   
  A 3D-printed scoop will retain powder on its walls after dumping, introducing dose error and
  cross-contamination between runs. Strategies ranked by complexity:                                            
                                                                                                                
  **Simple / materials-based:**                                                                                 
  - PTFE spray coating on the scoop interior (low surface energy, significantly reduces adhesion)               
  …[truncated]

### Issue #4 [OPEN]: Consider again the bimodal compliant mechanism feature as a secondary idea
In relation to #2 ; begin designing this. Download and install software that can help you run tests to check for bimodal compliance

### Issue #6 [OPEN]: Consider meta tools for CAD and such
@copilot I don't like this statement from https://github.com/vertical-cloud-lab/powder-excavator/pull/2#issuecomment-4309337047

> chosen over Rhino/Grasshopper, Fusion Generative Design, nTop, Onshape FeatureScript because it's pure-Python and pip-installable — none of the others survive the "freshly-cloned repo on a CI runner" test

You have a full dev environment. You should try to install each of these and if you really can't do anything meaningful within a 60-minute session, that's one thing - but show me. I want you to look at the context in that PR and not be so restricted to Python-only and pip-installable. It doesn't need to be Python necessarily, but it would be nice

### Issue #8 [CLOSED]: Create a bare bones latex template
Digital Discovery submission style. Use lorem ipsum. Install latex and compile And provide a direct link to the PDF in your replies

### Issue #10 [OPEN]: Search for commercial powder dispensing solutions
Include comprehensive list of company and product landscape. Send several Edison queries. Don't wait. Fetch next session.

### Issue #12 [OPEN]: Consider alternative styles/methods of powder dosing
I.e., something other than what's described in #2 or #5 that can still be put on the genmitsu 3018-pro v2 and can be implemented relatively easily (note that we have a makerspace but we only have a day left of the workshop -- introducing electronic/motor components is possible but introduces risk). 3D printing isn't a problem. After thinking a bit and considering the findings from #11 in terms of alternative methods, send an edison query asking for feedback. Don't wait. Fetch next session 

### Issue #15 [OPEN]: identify powders to use
![PXL_20260424_184018361.MP.jpg](https://github.com/user-attachments/assets/021602dc-95c4-4896-9d92-7b713da553f5)

![PXL_20260424_184042501.jpg](https://github.com/user-attachments/assets/5e3474cf-fb02-417e-a8fa-9ed8d008f62c)

![PXL_20260424_184036773.MP.jpg](https://github.com/user-attachments/assets/ca0d8764-732c-4b15-b49b-e9a63335276a)

![PXL_20260424_184031197.MP.jpg](https://github.com/user-attachments/assets/c96715ff-81e3-4584-a994-c5864d451148)

![PXL_20260424_184947360.jpg](https://github.com/user-attachments/assets/4378e724-1606-48c4-9436-1c68ff59af2e)




### Issue #17 [OPEN]: Use marp to create a project wrapup presentation
Consider all the issues. Include some of those funny pictures and gifs earlier on, excerpts (screenshots if possible) of key comments we made throughout. Especially highlight the before and after of giving it CAD tools and other instructions. Highlight the role of Edison scientific. Show the final design. Include the below two (image and video).

Keep in mind jean luc Doumont presentation principles (maximize signal to noise ratio, reduce noise on slides, "title area" is actually "message area" - put a complete sentence that is the message the slide should convey)

<img width="4032" height="2268" alt="Image" src="https://github.com/user-attachments/assets/b9da3ebe-c590-4ee5-ad5f-64dfeec8aea8" />

https://github.com/user-attachments/assets/bafa19e7-7323-45a9-b5bc-884478dbd095

At end, send slides (and associated image and video files) to Edison analysis for review and suggestions for improvements. Don't wait. Fetch next session

### Issue #20 [CLOSED]: Come up with a better name for this repository


### Issue #22 [OPEN]: Programmatic access to Bambu H2D


### Issue #24 [OPEN]: Identify parts for vibration motor and solenoid
We'll be incorporating this into #16 so it will need to be relatively small
We're planning on integrating the solenoid externally and then mounting some sort of vibration motor
We'd like to be able to vary frequency and amplitude on the vibration motor (if possible)
We plan to control this with a raspberry pi zero 2w, so we'll need potentially attachment boards or something like that to control it

### Issue #26 [OPEN]: Create a BYU NASA Space Grant application proposal narrative
This is for Sam Charles, an undergraduate. The guidelines for the proposal are fairly sparse, see below (also download and commit the application PDF to the branch you make). Begin by simply making a latex template for this - lorem ipsum style with a proper bib file setup. In this request and issue, we are *only* worried about the 3-5 page proposal, not any of the other requirements (e.g., letters of recommendation). Note that Sam is the one submitting it, so it should be framed around him and his project, the specific things he is and will be working on. FYI, the proposal is meant to be framed around generative CAD for this repository, tied into a larger vision of autonomous discovery of AM aerospace alloys (accurate powder dosing of many distinct powders with various characteristics being a critical component of that). However, start with the lorem ipsum version so I can double check that.

----

NASA SPACE GRANT FELLOWSHIPS
Description: The Utah NASA Space Grant Consortium Fellowship is offering up to $2,000* for undergraduate applicants, $4,000* for MS students, and $8,000* for Ph.D. students.

Application Requirements:

New Applicants

Fellowship application
Letter of recommendation from a faculty advisor
An additional letter of recommendation
Transcript (does not have to be an official transcript)
Proposal (3-5 pages)

Continuing Students

Fellowship application
Letter of recommendation from a faculty advisor
One-page report of current project status
Faculty advisor certification of the previous year's cost sharing.



All Students: All applications and attending items must be emailed to Lissa Matthews (lissa@byu.edu) by May 8, 2026

[NASA Fellowship Application](https://engineering.byu.edu/0000019c-fdd3-dc4f-adfe-fff75ee70000/nasa-26-pdf)

### Issue #28 [OPEN]: Background information on powder dispensing and generative CAD
To inform the background section of a grant proposal (#26), 
- research the state of powder dispensing in commercial and research sectors. Find examples and statistics of typical machines and use cases. Make a short list of recent, relevant academic papers that could be cited in the background section and beyond, along with a short summary of each.
     - reference #10 in your research
- Additionally, research the state of generative CAD design, and the research that has been done around it. Has this research space been explored as far as capabilities and limitations go? Make a similar list of sources and summaries.
     - reference #6 in your research
Find resources to be used in the background section of the proposal.

### Issue #30 [OPEN]: Brainstorming session on design possibilities
We need to start developing design ideas that meet the requirements of those mentioned in the proposal, specifically the hardware design requirements mentioned in section 4.2 (refer to #27). These ideas will incorporate the parts and features mentioned in #25 as well. Its worth mentioning here that with the powder doser being implemented into an autonomous loop, it is integral that the doser can meet the design requirements with as little human intervention as possible (ie: having to replace and clean the tube for each new powder being used). Whether or not this design requires multiple separate powder reservoirs and auger tubes or some other solution is to be determined. No sketches or cad designs are needed yet for this session, just a discussion on the different possibilities and their respective benefits and pitfalls.

### Issue #32 [OPEN]: Quotes and clarifications for powder dosing equipment (MTI, Mettler, etc.)
MTI 

- https://mtixtl.com/products/am-pd6 
- https://mtixtl.com/products/am-pd16
 - https://mtixtl.com/products/pf-a (and also ask about lead time)

> Manual Dispenser of 250 ml Made of Glass for Solid Powder - PF-A
> PF-A is a 250 ml manual dispenser for delivering solid powder. It is a cost-effective tool to weigh powder precisely with a balance Specification:  Container Material: The powder container is made ...


Labman
 
https://www.labmanautomation.com/portfolio/products/multidose/

Chronect XPR
https://www.mt.com/us/en/home/products/Laboratory_Weighing_Solutions/mettler-product-collaboration/axel-semrau.html 
https://www.youtube.com/watch?v=zm9fOt1J37c
 
@williamulbz can you work on getting quotes for the above 5 products?

### Issue #34 [OPEN]: Modular Single-Channel Powder Doser Design
This conversation is an off-shoot from #30 and the resulting PR #31. This repository is a good resource to access previous conversations, discussions, project goals for context, as well as outside software to download, i.e. for CAD or electrical design.

We've decided to move forward with Idea B from #31. While we're also interested in other ideas, like C, Idea B (a single-channel doser with integrated and dedicated electronics (motor, vibrator, tapper, angular something, etc.) that can be repeated N times to get the 30-powder volume we need) will allow us to not only rapidly prototype a working version, but also to use it as an archetype for later versions.

Don't forget that this design needs to be easily modular, scaling simply and quickly to 30+ powders. Also, it should use the auger design in this repository and fulfill all design requirements.

Idea C featured a single channel doser, similar to Idea B, but with swappable channels, so instead of one whole module per powder, it's one module with many channels, one per doser. We're still interested in this idea, so keep this kind of modularity in mind, but any actual design steps toward this idea will be made after the first prototype at least, so don't design for Idea C, just keep it as a consideration.

Move forward with Idea B. Devise a project plan/pathway to a prototype (including design requirements and steps), then execute your first steps. I want to see the plan and images/models of the designs. The basic workflow will be AI design-->printing-->testing-->feedback-->AI design and so on. So ideally, you would give us 3d files and instructions we can print and test to return with feedback for the next version.

Please, where possible, bring in models of the electronic components as well, making a full assembly of the overall design. Discussion #25 is relevant for parts selection. If there are parts or software you need and cannot find or download, make a list of requests and we can put those things in this repository for you to use. Similarly bring in mechanical parts like screws if needed--assemblies should be full and complete. 

### Issue #36 [OPEN]: Channel-Sealing Cap Design for Modular Powder Dosing
As we design this powder doser, a big step will be making it modular. One idea is for the channels to switch out, but not the mechanism, reducing cost and electrical complexity. This requires new mechanisms, and first and foremost is safety and cross-contamination. As channels are set into the mechanism, turned to release powder, and set back into the carousel or catalog or wherever they are stored (to be decided later), we need to ensure that no powder will spill, and that the channels can be safely stored without worry.

Using the conversations and tools in this repository, design a cap or sealer of some kind compatible with some version of the auger, which is central to this device. This might include some kind of linkage like a hatch, it could be screwed on/off, it could twist like a shutter, etc.--lots of options. Of course, designing this part/mechanism will likely require designing/adapting the auger/channel as well. Each design must still be able to fulfill all design requirements with an appropriate mechanism (out of the scope of this issue), including rotation, being tapped, vibrating, and being tipped to various angles. 

These new designs do not have to be independent--we want this process to be automated, so designs that require a reasonable addition/alteration to our non-modular designs are okay; adding a motor or a mechanism or both is fine, but adding something like a 6-axis arm is too much, and fails the design requirements through price and complexity. Our designs are still in process (see #34) so keep your designs generic for now, able to apply to a new system when we're ready. This is primarily brainstorming and proof-of-concept, including 3D printing and testing designs.

Start with descriptions and visual depictions (images, CAD models, etc.) of several ideas. Out of those ideas, I will choose, provide more input to move forward, and refine. I want to 3D print and test these once we hone down ideas.

Feel free to download things like CAD software to aid the design and communication processes. If you need extra help or any extra resources, make a list of requests I can add to the repository.

### Issue #40 [OPEN]: Determine individuals and organizations we could reach out to for help with powder dispensing
For example, people mentioned (or who participated) in https://accelerated-discovery.org/t/accurate-powder-dispensing-for-chemistry-and-materials-science-applications/177

Others mentioned in https://github.com/vertical-cloud-lab/powder-doser/pull/29

### Issue #42 [OPEN]: Determine individuals and organizations we could reach out to for help with generative CAD
See #7 #29; see also references from #27 ; various edison scientific queries across PR and repository. Can be authors of papers, companies, etc. Use Edison to help with the search. Get direct contact info whenever possible and include the link to the public source of that contact info.

### Issue #44 [OPEN]: Brainstorming session on electrical and software systems
We need an overview of the different approaches that can be taken to create the electrical and software system of the powder doser. #25 specifies the parts that would be used for this system, and #31 outlines the various ideas for how to integrate these parts into a multi-powder dosing system. For this initial brainstorming session, we will use design 2.2, the modular setup. A few things to include in this brainstorming session.

 - Note that #25 does not specify automated angle control yet, and it is still undecided how angle control will be handled. It can be assumed that some sort of servo, stepper, or linear actuator will be used for this function. 

 - The software will need to receive information about what powders will be mixed and their respective amounts. Each module will then need to be adjusted to the angle, tapping frequency, rotational speed, and vibration frequency that will allow it to dispense properly according to the identified powder. The microcontroller will have to communicate with the scale/load cell in a feedback control loop to ensure the proper amounts of each powder are dispensed. What would the electrical system look like to accommodate this? If any example schematics are needed to explain, use Kicad to do so.

 - How can each respective module with its controlling features (stepper, vibration, angle, and tapping) be controlled simultaneously and independently

 - How will we design it so that extra modules are easily added to the system both in software and electrical connections? This includes outlining the IO expansion capabilities of our chosen microcontroller

 - It would be helpful to provide small code samples for how certain features would be accomplished


### Issue #46 [OPEN]: Part-by-part Powder Doser Approach
To prototype the Powder Doser referenced in this repository, we are going to design the machine and parts and have you (@copilot) model them in CAD. You can look through this repository for context, but note that we are moving away from the designs in #34, so don’t assume the parts you’re modeling are for that—they’re not. We will then print the new parts on the lab printer, test them, and come back to you with feedback. 

Your first part/task (both as a test and as an important component) is to make a bracket according to the design shown in the picture below. It is similar to a shaft collar. It should have room for a screw on top to tighten. Its inner diameter should be the auger’s out diameter with some tolerance. We want the auger to be able to spin freely while still being held in place, so pick an appropriate tolerance for that performance. Additionally, there should be mounting holes as directed in the drawing, as well as the obvious holes to tighten the bracket. Dimensions are given in the drawing as well, and the printing face/orientation is indicated.

The intersection of the circular collar and the rectangular mounting plate could be a point of failure, so please curve that intersection to smooth that transition.

Return a ready-to-print STL file, along with a diagram of how it should work.

<img width="424" height="586" alt="Image" src="https://github.com/user-attachments/assets/1a930d05-5ea2-4926-89d7-ec49aea76abb" />

### Issue #48 [OPEN]: New Auger design with Integrated gear
@copilot Understanding the context from this repository and from your parent issue, and using the auger from #16 as reference, create a new auger design that features teeth, like a toothed gear, around the shaft about a third of the way toward the dispensing end. This will link with a gear attached to a stepper motor to allow the auger to rotate about its long axis. The teeth should not be inset into the auger, but should be outside, as if there was a gear interfering in a 3D modeling program. Below is a diagram to show intended results.

Importantly, no part of this new design can alter or interfere with the internal design of the auger. The internals should be exactly the same--only its external features should change. 

Make sure not to overwrite the auger designs found in #16.

Additionally, design the accompanying gear to fit onto a NEMA stepper motor, as defined in #24 and the accompanying #25. Report the gear ratio and accompanying parameters.

Return a new auger and gear design. As with all parts under this parent issue, we want the parts to be printer-ready so we can test and return with feedback as soon as we can.

<img width="1200" height="818" alt="Image" src="https://github.com/user-attachments/assets/2bd87d6a-332a-403a-900d-4ebcb5827d10" />

### Issue #50 [OPEN]: Tap Collar Design
@copilot I'm assuming you understand all the context from your parent issue. Go there for extra context if needed.

For our next part, we're making a tap collar. This is a collar that will sit rigidly around the auger and have an integrated coin vibration motor and solenoid to vibrate and tap the auger and help the powder flow better. We want this piece to be independent (not rigidly attached to the baseplate) but not fully rotate with the auger so cords don't get wound up.

 The first design we'll try is similar to the bracket, but with a separated mounting plate and a specific hardstop. See the picture below for context. The mounting plate will be basically the same as the brackets, but without the circular bracket part, and instead with a raised column to contact the collar and stop it from spinning. 

The collar is complementary; basically the same as a bracket, but without a mounting plate. The tabs at the top where the tightening screw is located will serve as the hardstop contact point. On this bracket, add places for a coin motor and solenoid to be mounted. 

All this should be clearly explained in the drawing below; the explanations above are just textual explanations of this drawing. Parts are labelled, but dimensions are not, as they should match the bracket designs in #46 and #47. Additionally, the coin motor and solenoid don't need to be arranged or mounted as drawn--those are just suggestions. 

Be careful as well of the holes on the mounting plate--we still need to be able to screw it in.

<img width="923" height="735" alt="Image" src="https://github.com/user-attachments/assets/7a9f5604-2e72-4597-9c43-c9b17dd24c4f" />

### Issue #52 [OPEN]: Designing a simple part with zoo.dev
@copilot This issue is a foray into using zoo.dev to generate CAD models. Use the API key to access zoo.dev's tools to complete these tasks.

Using the design below, model a bracket. This bracket should fit around the auger from #16 with some tolerance. It is similar to a shaft collar with a mounting plate. We're looking for 3D-print-ready parts, so make it somewhat polished and ready to go. 

Return 3D print ready files, along with a diagram of the Auger fitting into 2 brackets.

<img width="848" height="1171" alt="Image" src="https://github.com/user-attachments/assets/bd57cf67-70d6-487f-b244-9bddf8a29561" />

### Issue #54 [OPEN]: Designing a simple part with CADsmith
@copilot This issue is a foray into using [CADsmith](https://github.com/vertical-cloud-lab/CADSmith) to generate CAD models. Use the API key to access CADsmith's tools to complete these tasks.

Using the design below, model a bracket. This bracket should fit around the auger from #16 with some tolerance. It is similar to a shaft collar with a mounting plate. We're looking for 3D-print-ready parts, so make it somewhat polished and ready to go. 

Return 3D print ready files, along with a diagram of the Auger fitting into 2 brackets.

<img width="848" height="1171" alt="Image" src="https://github.com/user-attachments/assets/f9c1014f-d3d3-407a-8ff7-a5dcb0f6fba1" />


### Issue #56 [OPEN]: Designing a complex part with zoo.dev
@copilot For the powder doser, we have several pieces, but now we need a foundation onto which all parts can be fastened. Pulling from #46 and its sub-issues, design a mounting plate onto which we can mount all pieces (brackets, tap collar, NEMA motor, etc.). It should be as small of a form factor as can comfortably be allowed (i.e. not a lot of unnecessary material), should have accurate through-holes for mounting each piece, and be 3D-printable.

An additional and difficult part of this design is that it needs to rotate. Add a hinge in line with the dispensing point of the auger so that the dispensing point and hinges are an axis about which the mechanism can rotate, perpendicular to the auger's long axis. This presents a challenge because the hole in the auger is right in the middle, so a flat plane would cut the auger in half, and none of the brackets or motor would work either. And the powder still needs to dispense of course--it can't be blocked by the hinges or anything else on its way to the cup. You need to design a mounting plate that can accommodate all the parts in correct configurations while also hinging around the horizontal axis of the dispensing point (the hole). 

Underneath this large mounting plate will be a base plate. This base plate will house the other half of the hinge, along with another difficult piece: a linear actuator. Using a placeholder for the linear actuator, design a baseplate with a hinged connection to the mounting plate and linear actuator. The auger needs to be rotate between 0 degrees (horizontal, auger in line with the ground) and 90 degrees (vertical, auger perpendicular to the ground). 

Additionally, the baseplate must stand above the ground high enough to accommodate a cup and scale. Design the baseplate with some sort of stand, legs, or supports that can accommodate a scale and cup underneath it, which still accomplishing all other design requirements.

Return 3D-print ready files, a full assembly file and diagram (including a placeholder cup and scale), diagrams of how each piece should be installed (including labels for mounting holes), a diagram showing 0, 45, and 90 degrees of rotation about the hinges using the linear actuator, and a diagram showing powder flow through the auger to the cup. 

One crucial piece of this task is that it is also an exploration of zoo.dev's CAD modelling capabilities. Using the API key, use zoo.dev for this task. Return a short response about the pros and cons of using zoo.dev, informed by your experience through this process.

Good luck!

### Issue #58 [OPEN]: Designing a complex part with CADsmith
@copilot For the powder doser, we have several pieces, but now we need a foundation onto which all parts can be fastened. Pulling from #46 and its sub-issues, design a mounting plate onto which we can mount all pieces (brackets, tap collar, NEMA motor, etc.). It should be as small of a form factor as can comfortably be allowed (i.e. not a lot of unnecessary material), should have accurate through-holes for mounting each piece, and be 3D-printable.

An additional and difficult part of this design is that it needs to rotate. Add a hinge in line with the dispensing point of the auger so that the dispensing point and hinges are an axis about which the mechanism can rotate, perpendicular to the auger's long axis. This presents a challenge because the hole in the auger is right in the middle, so a flat plane would cut the auger in half, and none of the brackets or motor would work either. And the powder still needs to dispense of course--it can't be blocked by the hinges or anything else on its way to the cup. You need to design a mounting plate that can accommodate all the parts in correct configurations while also hinging around the horizontal axis of the dispensing point (the hole). 

Underneath this large mounting plate will be a base plate. This base plate will house the other half of the hinge, along with another difficult piece: a linear actuator. Using a placeholder for the linear actuator, design a baseplate with a hinged connection to the mounting plate and linear actuator. The auger needs to be rotate between 0 degrees (horizontal, auger in line with the ground) and 90 degrees (vertical, auger perpendicular to the ground). 

Additionally, the baseplate must stand above the ground high enough to accommodate a cup and scale. Design the baseplate with some sort of stand, legs, or supports that can accommodate a scale and cup underneath it, which still accomplishing all other design requirements.

Return 3D-print ready files, a full assembly file and diagram (including a placeholder cup and scale), diagrams of how each piece should be installed (including labels for mounting holes), a diagram showing 0, 45, and 90 degrees of rotation about the hinges using the linear actuator, and a diagram showing powder flow through the auger to the cup. 

One crucial piece of this task is that it is also an exploration of CADsmith's CAD modelling capabilities. Using the API key, use CADsmith for this task. Return a short response about the pros and cons of using CADsmith, informed by your experience through this process.

Good luck!

### Issue #60 [OPEN]: setting up test module electronics
To test our module, we want to set up an electrical and software system that allows for easy testing of different configurations of dispensing angle, tapping, vibrating, and auger rotation. This system does not need to be able expandable to 30 modules yet, and preferably can run off one microcontroller. The parts to integrate are outlined in #25. create a KiCad schematic of what this simpler system would look like, assembly and wiring instructions (including pin locations and nets), and provide code for the appropriate microcontroller to run this test module with easily adjustable configurations. 

### Issue #62 [OPEN]: Mounting Plate Design
@copilot Look over and understand the parent issue and context. The parts we are designing for are the parts in this parent issue and its sub issue.

We need a baseplate, the board that all the other components attach to. Below is a drawing of what it should look like and layout.  Green plus signs indicate mounting points (holes), as well as the axis of rotation. There are no dimensions indicated--you should figure out the dimensions based on the existing parts, i.e. the motor gear needs to interface with the auger gear, so the motor mounting block has to be a resulting distance away.

There is a hinge at the base of the mounting plate. I have included design for the hinge, including a bit of the base plate it will attach to and a diagram of the mounting plate at 0 and 90 degrees. Again, dimensions are up to you.

There is a bit of unnecessary space indicated that you can remove if you like. If you have any specific questions, list them.

Return a baseplate CAD model ready for 3D printing, plus an assembly showing how each part fits in. Include as well an engineering drawing, listing all relevant dimensions, including thicknesses and distances between mounting holes.

<img width="1226" height="1720" alt="Image" src="https://github.com/user-attachments/assets/060859ea-7ddc-4884-9037-7f73ad083a9a" />

### Issue #64 [OPEN]: Run initial test with solenoid, checking to see if it provides enough impulse
Per comments from @swcharles and @williamulbz 

If impulse isn't enough, consider DC stepper motor with finger or similar

### Issue #65 [OPEN]: Adding servo angle control to mounting plate and baseplate
Using the current designs for the baseplate and mounting plate from #57, we need to add a gear to one of the hinge edges that will interface with a servo motor. We will use an MG 996R for the time being. Dimensions can be found here https://towerpro.com.tw/product/mg996r/

The servo should be mounted to the baseplate, just next to the hinge on one of the sides. The gear ratio between the hinge gear and the servo gear will be 2:1 in order to reduce the torque load on the servo. The gear on the mounting plate is not its own part, it is part of the mounting plate located on the hinge axis. 

Before adding the gears, ensure that the baseplate does not interfere with the geometry of the mounting plate. In its current state, the hinge stands intercept the mounting plate when it is folded down, flush to the baseplate. Look at the reviews for #57 to understand what the hinge stands should look like. Do a check that the two parts are not interfering with each other and that there are no floating bodies before submitting changes.  

### Issue #67 [OPEN]: fixing insides of geared auger
The geared auger most recently produced in #49 has a small issue that needs to be resolved. The exit hole has a cone feature that converges with the central shaft. The powder is intended to travel by way of the archmedes screw and eventually out the exit hole. The issue is that the cone feature intercepts the central shaft and thus closes off the path of the archimedes screw so that the powder can never escape. This needs to be recreated, keeping all other features of the part the same, but also has an exit hole connected to the path of the archimedes screw. 

### Issue #69 [OPEN]: Explore use of OCP CAD Viewer VS Code extension for CadQuery
https://marketplace.visualstudio.com/items?itemName=bernhard-42.ocp-cad-viewer

I.e., coding locally in VS Code while adjusting CadQuery scripts and visualizing them in real-time. Seems pretty similar to our OnShape workflows such as in https://github.com/vertical-cloud-lab/powder-doser/pull/7#issuecomment-4482580394, but with tighter feedback cycles.

I came across https://github.com/CadQuery/CQ-editor (a GUI for CadQuery) which got me thinking about whether VS Code might have an extension.

### Issue #72 [OPEN]: Record of Prints and Assemblies
This is a place to record the constructed designs and give feedback.

### Issue #73 [OPEN]: Record of Designs
@copilot we want this issue to be a record of every design we have collectively made so far in this repository, i.e. any design you have made/iterated based on a user comment or review, etc. This includes every commit, every design after every comment, every issue and pull request, etc. Go through all the activity in this repository from its inception and create a file (or several) here to chronologically document all designs from this repository. This means you will have to go through every issue, pull request, comment, and commit, etc. We want it chronological, not project based, i.e. make comments for and list all designs in order of creation, don't put all augers together or all mounting plates together. This can be done in one big markdown file, or however else you think is prudent. However, it should be scrollable and easily viewable, i.e. separate files for each design would be bad, so one markdown file is probably best.

Make one comment/entry for each design. Each entry should include 1-3 good visuals of the design and a 1-2 sentence summary of the design, what changed, and why the changes were made (based on the comments and/or review that started the new session and design). This can include diagrams and even drawing I've supplied but should specifically include render views to accurately communicate designs. This will be a lot of comments and a lot of images, which is the point--a full record we can scroll through to quickly and simply see the progress of design throughout this process. We recognize that this will include many repetitions of objects, for example, while we only have one issue/PR for the bracket design, I want every iteration of the bracket design on here, placed correctly in the chronological list of when they were created.

If for any reason you are unable to complete this request, return a short but detailed explanation why.

### Issue #75 [OPEN]: Literature search for generative electrical / PCB design
Send a set of 5-10 high effort literature edison scientific queries. Before sending the queries, have a look at the various queries sent in https://github.com/vertical-cloud-lab/powder-doser/issues/28 and https://github.com/vertical-cloud-lab/powder-doser/pull/29, taking a look at all raw committed Edison Scientific trajectories/artifacts, noting that those are for generative CAD, and we're looking to expand that background/literature search to generative electrical design and PCB design. Also have a look at the context in https://github.com/search?q=repo%3Avertical-cloud-lab%2Fpowder-doser+kicad&type=issues and https://github.com/search?q=repo%3Avertical-cloud-lab%2Fpowder-doser+kicad&type=pullrequests, where kicad is mentioned. Maybe there are other tools than kicad that are in scope for this; you could dedicate one query to what state-of-the-art tools are available.

Wait and fetch this session.

### Issue #77 [OPEN]: Utah AI Convergence event abstract and poster
Information given on the event and attached links for more info:

"The College of Engineering AI Committee is hosting the Utah AI Convergence event on June 23-24 in the Law School Building (https://www.price.utah.edu/ai/convergence-2026). On behalf of the organizing committee, we would greatly appreciate if you could please consider having your students submit abstracts (eventually, posters) on their research that uses or advances AI to the Student Poster Competition. Last year, we had 60+ posters competing for 4 prizes. Additionally, we will invite a certain number of submitted abstracts for lightning presentations. Prizes will be awarded to the best three lightning talk speakers.

Here is the call for submission - https://admin.coe.utah.edu/fill-form/2026-ai-poster-submission

Note that the deadline for submitting poster abstracts is June 2, 2026. The word limit for the main text of the abstract is 500 words. Hopefully, your students would not find submitting abstracts too burdensome by this deadline (we can extend the deadline a few days, if needed). Preliminary work submission would be fine as well."

We want to create an abstract to submit for our poster for now. Within the 500 word limit, we need to summarize our goals for our project, similar to what was done in #26, with an emphasis on how we are researching the use of AI in generating designs. It would be good to briefly summarize how we have used it so far and what we have learned about using it for designing our powder doser.



### Issue #80 [OPEN]: Measuring Auger Volume
@copilot suggest methods for measuring the maximum possible volume of each auger, focusing on Auger Type 4 as described [here](https://github.com/vertical-cloud-lab/powder-doser/issues/48#issuecomment-4513155870). Also, select the best method and calculate powder capacity for Auger 4.

One suggested method is using cad tools, but the engineers on this project are trying to use cad software as little as possible, so avoid that solution if possible.

If possible, this measurement would be a function of length, i.e. we would know that a 5in auger has x powder capacity

## PULL REQUESTS

### PR #2 [OPEN]: Initial design diagram, brainstorming, and open parametric CAD pipeline for powder-excavator
- [x] Re-render CAD assembly + part SVGs/PNGs after geometry changes
- [x] Submit Edison analysis bundling current design state
- [x] Edison query status checked: prior-session task `ac68bc56…` not pollable from this session's API token (per-session permissions); per user instruction "if not, don't wait" — proceeded without blocking
- [x] Fold PR #7 primary recommendations into this PR's docs (`cad/README.md` + `README.md`):
  - [x] Replace blanket "all the others fail the fresh-runner test" dismissal with PR-#7's evidence-backed scoreboard summary (Rhino/Compute, Onshape, nTop, Fusion GD)
  - [x] Add cost / Linux-headless reality table for the paid tools (Rhino academic ~$195 Win/Mac-only, Onshape free Public + free Education plan, nTop quote-only)
  - [x] Add "Target hardware and matched toolchain" section: Genmitsu 3018-Pro V2 (GRBL CNC) + Prusa MK3 / Ender (FDM); PrusaSlicer CLI for FDM, FreeCAD Path / Kiri:Moto → GRBL for CNC, Camotics / NC Viewer for sim, UGS / bCNC sender
  - [x] Tighten the design-space-exploration recommendation: manual sweeps + pandas/Jupyter scorecard by default; Optuna only past ~5 parameters and ~15+ physical builds; Ax/BoTorch + Science-Jubilee held on the *future* SDL wishlist
  - [x] Mention split FDM-vs-CNC DFM as a planned `cad/dfm.py` direction (no code change yet)
  - [x] Add `build123d` as a sibling pick to CadQuery (same OCCT kernel) and OpenSCAD as non-Python second source
  - [x] Reference Edison literature-synthesis task `c0f412d3-…` (already returned, archived in PR #7) explicitly
- [x] Re-run `cad` unit tests (9/9 pass) and `cad.dfm` (28 checks, 0 failures)
- [x] `parallel_validation` (Code Review + CodeQL) clean — review-comment fixes (vague Edison reference, missing dot in filename) applied

### PR #5 [OPEN]: Add bimodal compliant mechanism design + bistability checker + 3D-printable prototype
- [x] Fix the "floating object" geometry bug in `cad/bimodal_trough.scad` (flexure now climbs from foot to apex; STL/iso PNG/spin GIF re-rendered).
- [x] Address PR review thread feedback:
  - [x] `scripts/robustness_sweep.py` — drop the `--thick-tol` claim from `InputRanges` docstring (no such CLI flag exists) and remove unused `scale` from the `render_violin()` zip.
  - [x] `scripts/visualize_bimodal.py` — add `_require_bimodal()` helper so `render_static()` and `_snap_trajectory()` raise a clear `ValueError` (with the analyser summary) instead of crashing with `IndexError` when the design is mono-stable.
  - [x] `tests/test_robustness_sweep.py` — use `pytest.approx` for the LHS reproducibility check so it survives minor cross-version FP drift while still catching nondeterminism.
  - [x] `tests/test_beam_fea_crosscheck.py` — relax the strict `len(results) == 9` assertion to "≥ 80 % of requested points converged + still brackets both wells", matching `run_sweep`'s documented best-effort behaviour.
- [x] `pytest tests/` still green (23 passed, 1 skipped).

### PR #7 [OPEN]: Exploring different ways of doing generative CAD, including command line interfaces and open source CAD tools
- [x] Add `cad/meta-tools/onshape_classroom_upload_test_probe.py` — uploads a tiny test STEP (20×10×5 mm plate, 34 KB) into a fresh `Powder Doser — classroom upload test` Onshape document via the same `onshape_upload_assembly` helpers, then re-fetches the document metadata to verify the classroom-ownership + public defaults
- [x] Test run: document created, `public: true` ✓, `owner.type: 1` (COMPANY) ✓, `owner.name: 'Vertical Cloud Lab'` ✓, 1 element uploaded
- [x] Redacted summary committed to `logs/onshape-classroom-upload-test.summary.txt`

### PR #9 [MERGED]: Add bare-bones Digital Discovery LaTeX template
- [x] Reorder end-matter to Data availability → Conflicts of interest → Acknowledgements → Notes and references
- [x] Drop optional "Author contributions" section
- [x] Add TODO markers next to title, author list, DOI, ESI footnote, abstract, affiliations
- [x] Rebuild `paper/main.pdf`
- [x] Address PR review feedback (round 1):
  - [x] Un-vendor third-party LaTeX packages and rely on TeX Live
  - [x] Switch to `extarticle` `9pt`; replace `sectsty` with inline `\@startsection` redefs
  - [x] Pin `\usepackage[version=3]{mhchem}`
  - [x] Rewrite `paper/NOTICE` to scope RSC attribution to RSC-only files
  - [x] Update `README.md` build instructions
- [x] Address PR review feedback (round 2):
  - [x] Fix inverted `doi empty$` conditional in `format.doi` of `paper/rsc.bst` so DOIs are emitted when present (not when missing)

### PR #11 [OPEN]: Submit Edison queries for commercial powder dispensing landscape
- [x] Inventory commercial platforms named in `research/commercial-powder-dispensing-landscape.md` and second-batch queries
- [x] Create `research/images/` with one representative image per platform (sourced from vendor / reseller / brochure pages) — **40 images** covering bench-top dispensers (Mettler Toledo Quantos, Chemspeed SWING/FLEX/Crystal, GDU-S SWILE, GDU-Pfd, Unchained Labs / Freeslate, Symyx), liquid-handling / balance platforms (Hamilton STAR, Tecan Fluent / Freedom EVO, Zinsser Lissy, Gilson PIPETMAX, Sartorius Cubis II, Analytik Jena CyBio FeliX, Anton Paar MCR), industrial LIW / bulk handling (Coperion K-Tron KT20 + MT12, Schenck/AccuRate, Brabender, Gericke GAC, GEA Buck, Glatt, Hosokawa Micron, Acrison, Hapman, AZO COMPONENTER, PSL GFD, Matcon), MTI Corporation lab + MTI Mixer industrial, Hou-2024 micro-feeders (MG2, 3P Innovation, LCI Circle Feeder MD-120, DEC µPTS, Vibra-Flow), and acoustic / piezo platforms (EDC Biosystems, Beckman Echo, Scienion sciFLEXARRAYER)
- [x] Add `research/images/README.md` (and `_manifest.json`) with per-image source URL + license / use-rationale notes (README image table is regenerated from the manifest so filenames and URLs stay in sync)
- [x] Replace user-flagged / clearly-wrong images with better vendor-sourced photos:
    - `chemspeed-swing` (was glass tubes / pipette → real SWING workstation, automationchemistry.com)
    - `unchained-labs-freeslate` (was Sunny Trident microfluidic chips → Freeslate Junior workstation, unchainedlabs.com)
    - `chemspeed-flex` (was generic Bing thumb → real FLEX workstation, labtim.si)
    - `zinsser-lissy` (was a generic worldwide-location banner → real Lissy robot, medicalexpo Zinsser product page)
    - `mettler-toledo-quantos-qx96` (was an unrelated MR204 reseller balance → real QX96 carousel, banebio.com)
    - `mettler-toledo-quantos` (was a 10 KB thumb → larger QB-P/XPE205 product photo, labmate-online.com)
- [x] Build a **compact, journal-style mosaic** of all 40 panels in [`research/images/mosaic.png`](research/images/mosaic.png) (2094 × 2528 px, ≈7" × 8.5" at 300 dpi, 7-column layout suitable for a 2-column manuscript figure), grouped into 6 colour-coded category banners (bench-top dispensers; liquid handlers / balances; industrial LIW & bulk; the two MTIs; specialised micro-dose feeders; acoustic / piezo) with (a)–(an) panel chips and short labels, plus a corresponding figure caption with per-panel source URLs in [`research/images/mosaic_caption.md`](research/images/mosaic_caption.md). Linked from the landscape doc.
- [x] Re-submit the stuck second-batch Edison queries. After the first re-run of `mti-corporation-lab-powder-equipment` (`6ca69e07-…`), the user rotated the API key, so all 6 still-pending queries were re-submitted under the new key. New task IDs are recorded in `resubmissions[]` in `research/edison_queries.json` (originals preserved):
    - `mti-corporation-lab-powder-equipment` → `ab9e026e-946d-4918-a0b6-49e09d7bc962`
    - `mti-mixers-industrial-powder-handling` → `e2919d20-86cc-44eb-a1f0-d2fc5b2db4f3`
    - `industrial-bulk-vendors-acrison-hapman-azo-psl-matcon` → `a61e05d3-46bd-4439-a599-1a143995adcd`
    - `lab-liquid-handlers-with-powder-modules` → `d2f50d5d-4448-4ed7-80e9-8bb28ed60313`
    - `acoustic-piezo-capacitive-microdose-and-quantos-qx-chemspeed-powdernium` → `78d179da-e724-4999-bb74-98a175944d6b`
    - `academic-and-open-source-powder-dispensing-robots` → `7b5e41fa-f5a9-4dba-bd79-75eaaca83ca3`
- [x] **Fetch the 6  …[truncated]

### PR #13 [OPEN]: Brainstorm alternative powder-dosing styles for the 3018-Pro V2, submit Edison feedback query, incorporate the result, add a preliminary CAD design for the top-ranked sieve cup, refine each A–H alternative individually, add annotated explainer panels...
- [x] Brainstorm A–H alternative dosing concepts + Edison literature query
- [x] Fetch Edison literature result + fold critique into brainstorm
- [x] Preliminary CAD design for top-ranked sieve cup (A + G) + anvil
- [x] Per-concept refinement A–H (SCAD → STL → admesh → iso/cutaway → spin → slice)
- [x] Per-concept annotated explainer panels + 4×2 composite
- [x] Per-concept 2-D dispensing animations + 4×2 composite (synced shared `Stage` + phase clock)
- [x] Merge `origin/main` into PR branch — resolved `README.md` conflict (kept both PR's alternative-dosing links and main's POSE presentation link + `paper/` LaTeX section); merge commit has both parents (HEAD = PR tip, MERGE_HEAD = main).
- [x] **Fix Edison upload API**: `create_task(files=…)` expects `data_entry:{uuid}` URIs returned from `client.upload_file()`, not raw local paths — that's why all 4 prior `JobNames.ANALYSIS` tasks failed Edison-side. Switched `docs/alternative-dosing/submit_edison_analysis.py` to upload-then-submit so attachments are actually delivered.
- [x] **Ground animations in physical CAD** (per @sgbaird-yolo): added `scripts/scene_world_frame.py` (single `WorldFrame` in mm + single `SideProjector` shared by every concept), `scripts/scene_cad.py` (CadQuery 3-D scenes per concept A–H placed in the shared world frame; STEP exports + AABB manifest under `cad/alternatives_cq/`), and `scripts/animate_dispensing_cad.py` (per-concept + composite GIFs projected from CAD AABBs through the shared projector — bed line, vial mouth, gantry rail and mechanism column line up across all eight tiles by construction; 10 mm scale bar proves the transform is metric).
- [x] Resubmit Edison analysis with the corrected upload API (task `21fc2fa1-…`, 106 attachments including new CadQuery scenes, STEP files, manifest, and CAD-grounded GIFs) and fold the returned critique into `docs/alternative-dosing/edison_analysis_result.{md,json}`.

### PR #14 [MERGED]: Edison v4 design-review query + document data_entry upload flow
Submit the requested follow-up Edison analysis-mode query (iso PNG + SCAD + scripts + figures uploaded), archive the response, and codify the file-upload API in the agent instructions after two failed attempts revealed the local-path footgun.

- **`docs/edison-research/15-bimodal-trough-design-feedback.md`** — verbatim prompt + answer for trajectory `c829f7db`. The Crow critique is unflattering: PRBM treats the flexure as a pin-jointed von Mises truss, but the SCAD prints a clamped-clamped shallow arch with $h/t = 0.6/0.6 = 1.0$, well below the Qiu–Lang–Slocum bistability threshold of 2.31 — corroborated by `bimodal-beam-fea-crosscheck.json` showing only one zero crossing. Also flags that the lower well sits 1.9 mm below the base plate (physical collision) and that `tilt_per_y=60` is a viz mapping with no geometric counterpart, so vertical actuation cannot dump powder. Concrete next-iter knobs proposed: `flex_arch_kick` 0.6→≥1.5 mm, `flexure_thick` 0.6→0.4 mm, `flexure_width` 8→10 mm, `half_span`→30 mm, asymmetric offset-pivot flexure, central push-boss, base-plate cutout, 45° spill chamfer, swap PRBM for the shallow-arch model.
- **`docs/edison-research/README.md`** — index entry 15.
- **`.github/copilot-instructions.md`** — document the two-step Edison upload flow. `client.create_task(..., files=[local_paths])` silently fails with `status='fail'` and `failure_reason=None`; `files=` requires `data_entry:<uuid>` URIs from `client.upload_file(...)`:

  ```python
  uris = [client.upload_file(file_path=p, name=Path(p).name) for p in paths]
  task_id = client.create_task(TaskRequest(name=JobNames.ANALYSIS, query=...), files=uris)
  ```

No code, test, or figure changes — docs only.

### PR #16 [OPEN]: Add initial Archimedes auger attachment CAD (OpenSCAD)
One-piece rotating helical dispenser: 20mm OD, 100mm height, M3 spindle mount at top, 2.5mm exit hole at bottom. Parametric OpenSCAD file, renderable at openscad.org/demo without install.

### PR #18 [OPEN]: Add Marp project wrap-up presentation (recreating the manual deck), host on GitHub Pages, and apply Edison analysis feedback
- [x] Initial deck, HTML + PDF builds, Edison submission script
- [x] **GitHub Pages** workflow at `.github/workflows/pages.yml` deploys `slides.html` on push to `main` **and to `copilot/use-marp-create-project-wrapup-presentation`** so the deck can be previewed from this PR branch without merging
- [x] **Fetched Edison task `df8efb13…` and applied the feedback** (archived at `presentation/edison/df8efb13-feedback.md`)
- [x] **Reviewer-thread follow-ups**:
  - `submit_to_edison.py` now **fails fast** (non-zero exit) if any required file is missing, before calling `create_task()`
  - Capitalized "Jean-Luc Doumont" in both `presentation/README.md` and the Edison-submission prompt
- [x] **Re-aligned deck narrative** to credit the actual team (time-sorted instruction/comment review at `presentation/edison/timeline.md`):
  - Title slide lists the team — *Sterling Baird · Devora Najjar · Ron* — with a non-intrusive credit to Nasa for the Ultimaker print
  - Devora's authorship of issue #3 and PR #16, and the three-person "Devora, Ron, and I talked" pivot from issue #1, are surfaced on the relevant slides
- [x] **Recreated the manually-presented Google Slides deck in Marp** (per reviewer request):
  - Downloaded the source deck via Google's `export/pptx` endpoint and extracted all 15 embedded images into `presentation/assets/manual-deck/`
  - Rewrote `presentation/slides.md` as a sparse, image-driven 12-slide deck matching the manual narrative (auger hero → auger CAD → first-sketch pivot → revised cam pivot → 3-view cam-scoop drawings → 7 powder candidates → manual scooping ×2 → bistable trough render → bistable energy landscape → commercial landscape → 8-concept tile)
  - Each slide carries a one-sentence Doumont message-title; bodies are image-only, mirroring the "sparse on text, mostly based on what we said" style of the original
  - Reuses existing `mechanism.gif`, `bimodal-mechanism.gif`, `composite-spin.gif`, and `final-print-on-ultimaker.jpg` where they match the manual deck's media
  - Adds a `.cols3` style for the 3-up engineering-drawing slide
  - Renamed lingering `powder-excavator` references to `powder-doser` in `slides.md` and `README.md`; trimmed README paragraphs that referenced the removed print-video slide
  - Rebuilt `slides.html` and `slides.pdf`
- [x] **Pulled in the three YouTube videos that were embedded in the Google Slides deck** (extracted from the `.pptx` slide relationships): title slide → POSE 2026 walkthrough (`0CAu-x3wXns`); hand-scoop slides → "Pouring xanthan gum" (`VAltAawtkA4`) and "Pouring rice flour" (`IMuK3LTAWLM`). The photo on each of those three slides is now a clickable hyperlink to the corresponding YouTube video, with a visible `▶ … youtube.com/watch?v=…` caption so the PDF carries the URL too. Rebuilt `slides.html` and `slides.pdf`.

### PR #19 [OPEN]: Document candidate metal powders, dispensing targets, and surrogate-powder shopping list for the powder-doser
Captures the set of powders we intend to dispense with the powder-doser, together with handling/storage constraints and the custom-Al-crucible dispensing target. Following discussion on the PR, the document now leads with the real metal feedstocks rather than food-grade flow surrogates, and a separate buy-list for the surrogate set has been added for procurement.

### Changes

- **`docs/candidate-powders.md`** (new): scope is now the actual metal feedstocks of interest, with the food-grade surrogate set demoted to a brief deprioritised note.
  - Primary targets: high-purity Si and AlSi10Mg.
  - Broader element palette: the 15-element BYU VCL digital-alloy-lab set, with a pointer to `vertical-cloud-lab/digital-alloy-lab-private` for the canonical list and a placeholder best-guess palette (Al, Si, Ti, V, Cr, Mn, Fe, Co, Ni, Cu, Zn, Zr, Nb, Mo, + 1 TBD) to be overwritten once the list is shareable.
  - Handling/storage: desiccator-based dry-powder workflow for the ~1–2 month window before an inert atmosphere is available; ambient T/RH logging; treat the doser itself as humidity-sensitive during bring-up.
  - Custom Al crucibles: new section capturing dispensing targets as open machining work (geometry, alloy grade, batch size, machining route), with crucible drawings to live under `design/cad/` when produced.
  - Earlier food-grade surrogate set (rice flours, sodium alginate, calcium lactate, CMC, xanthan gum, even-mix) kept only as cheap stand-ins for mechanical debug, not as a driver for design decisions.
  - All LaTeX-style `--` dashes replaced with en dashes for ranges (e.g. 20–45 µm), single hyphens for alloy designations (e.g. Ti-6Al-4V), and em dashes for parenthetical clauses, per the PR review.
- **`docs/candidate-powders-shopping-list.md`** (new): buy-list for the six food-safe surrogate powders, addressing the request to produce a shopping list with validated links and prices.
  - Quick-reference table (powder, pack size, indicative USD, primary vendor) plus a per-item section with a vendor product link, an alternate Amazon SKU where applicable, and a one-line rationale.
  - Vendors used: Bob's Red Mill (rice flours, xanthan gum) via Amazon/Walmart/Target, Modernist Pantry (sodium alginate), Cape Crystal Brands (calcium lactate, CMC).
  - Prices spot-checked on 2026-05-12 (~$55–67 USD subtotal for one of each, before tax/shipping); doc explicitly flags that prices/stock fluctuate and the live product page is the source of truth.
  - Notes on hygroscopy/desiccator handling on arrival, and a direct ping to @swcharles to place the order if the items/pack sizes look right.
  - Cross-linked from `candidate-powders.md` under the "Earlier surrogate-powder set" section.
- **`README.md`**: link updated to reflect the new doc scope.

No code paths are touched.

### PR #21 [MERGED]: Propose new repository names and gather Edison Scientific feedback
The repo `vertical-cloud-lab/powder-excavator` needs a better name. This PR collects candidate names and submits them to Edison Scientific for ranked feedback (poll running async; result to be appended once returned).

### Candidates

Ranked by how well they evoke the project (a powder-excavating instrument from the Vertical Cloud Lab) while staying memorable:

- **NimbusMiner** — "nimbus" (cloud) + miner; ties directly to Vertical Cloud Lab
- **CumuloDredge** — cumulus + dredge
- **StratoScoop** — vertical/aerial powder collection
- **PowderProspector** — mining/prospecting fram

### PR #23 [OPEN]: Document programmatic and remote printing options for the Bambu Lab H2D
- [x] Document the three viable submission modes (Cloud / LAN+Developer / Bambu Connect) with primary-source citations
- [x] Survey open-source Python libraries and flag H2D-untested status
- [x] Reference AC `ac-dev-lab` A1-mini prior art and call out what carries over to H2D
- [x] Add "Remote slicing (STL → 3MF)" section with `bambu-studio --slice` and OrcaSlicer CLI flows
- [x] Empirically verify CLI (P2S happy path + H2D Manual filament-map → 36 KB IDEX 3MF)
- [x] Add bringup checklist Steps 0–6 (LAN, smoketest, FTPS+MQTT dry run, bambulabs_api, remote/Colab, Pi-side slicing)
- [x] Win/macOS reachability variants + concrete hardware-interlock options
- [x] Address copilot review thread (pullrequestreview-4269221079)
- [x] Diagnose ctrhjk's `FTPS ERROR: timed out` → switch stdlib `FTP_TLS` to `ImplicitFTP_TLS` subclass (port 990 is implicit FTPS)
- [x] Address ctrhjk's follow-up `522 SSL connection failed: session reuse required` → override `ntransfercmd` to wrap data socket with `session=self.sock.session`, pin SSLContext to TLS 1.2 (H2D's FTPS server doesn't implement TLS 1.3 session tickets), add troubleshooting subsection

### PR #25 [OPEN]: Identify parts for auger drive, vibration motor, and solenoid (with KiCad schematic)
- [x] Audit every URL in `hardware/vibration-motor-and-solenoid.md`
- [x] Replace dead LRA, fix StepperOnline URLs, drop NXDOMAIN psc.me.byu.edu, add wiper-style auger-tilt servo subsection + BOM items 16 / 16-alt / 17
- [x] Promote Pololu #3776 shunt regulator to required BOM item 18 and refresh totals
- [x] Mirror upstream vendor CAD / PCB / drill-guide files under `hardware/vendor-files/<part>/` with licenses, plus a README index
- [x] Replace OOS Adafruit #352 with Mean Well GST60A12-P1J + Digi-Key cart (items 13 / 13a / 13b)
- [x] Organize manual-downloaded vendor files into per-part subdirectories with `SOURCES.txt` + `SPECS.md`
- [x] Add baseplate-tilt linear actuator (per-system, horizontal ↔ vertical aim) per Will's comment on #24: BOM items 19 (Glideforce GF01-121010-1-66 / Pololu #4467, limit-switch variant), 19-alt (generic Amazon clone), 20 (second DRV8871); new subsection with stroke/force sizing, DRV8871 wiring, `gpiozero` stub
- [x] Add a "Pi Zero 2 W GPIO budget & PWM availability" section answering whether everything fits on a single Pi Zero 2 W: documents the 2 hardware-PWM channels (GPIO12/18 + GPIO13/19) plus DMA-backed software PWM on any pin, a full pin-assignment table for the default Tic T500 + solenoid + tilt servo + baseplate-actuator config (6 GPIOs used, 20 free), the GPIO delta for the DRV8825-alt path (+3 GPIOs for STEP/DIR/~ENABLE), and the PWM0-sharing rationale for the solenoid + tilt servo. Reassigned the baseplate-actuator IN1/IN2 pins to GPIO5/6 to avoid collision with the DRV8825 stepper path.
- [x] Add a "Servo-driven baseplate tilt — alternative to the linear actuator" subsection per Will's PR #25 review comment: stall-torque sizing math (≥ 20 kg·cm needed at the hinge for N-channel scale-up), four 180°/metal-gear servo suggestions (DS3225MG default, Hitec HS-805BB conservative, DS3218 budget, Savöx SV-1270TG high-end), 1:1 hinge-axis mount notes, and a full MCU/architecture-2.2-from-#45 impact analysis (PWM1 on GPIO13 for the tilt servo, −1 net GPIO vs. linear actuator, BOM −$67.45, one dedicated 5–6 V buck added because a 20 kg·cm digital servo's stall current would brown out the Pi's existing D24V22F5).

### PR #27 [OPEN]: Add BYU NASA Space Grant 2026 proposal: 5-page submission-ready narrative with figures, real references, Edison-guided readability pass, and summer-block week-by-week timeline
Scaffolds and populates the proposal narrative for Sam Charles's 2026 Utah NASA Space Grant Consortium Fellowship application. Initial commits delivered a lorem-ipsum scaffold so formatting, length, and bib plumbing could be reviewed; subsequent commits replaced that with a first-draft narrative built from Sam's outline, trimmed to a strict 5-page version per Sam's answers, incorporated Sam's and William's inline review feedback (figures, real references, mg accuracy, no issue refs, etc.), relaxed the layout back to the **full 5-page program maximum** (Sam preferred the earlier version that "had room to spread out"), applied a final readability pass driven by the Edison Scientific ANALYSIS results, and the latest commit adds a companion week-by-week summer-block planning document.

### `proposals/byu-nasa-space-grant-2026/`
- **`proposal.tex`** — `article`, 11pt, 1 in margins with looser `parskip` / `titlespacing` so the narrative spreads out across the full page envelope. Uses `natbib` + `hyperref` + `titlesec`/`fancyhdr` + `enumitem` + `multicol` (for the 2-column references list). Title block names Sam as the sole applicant and Sterling Baird (BYU) as faculty advisor; running header identifies him + page X of Y. Sections: Introduction & Motivation, Project Objectives, Approach & Methods (Generative CAD pipeline & AI–engineer roles / Hardware design targets / Validation & integration with the discovery loop), Timeline & Deliverables, Broader Impact & Relevance to NASA. The standalone Qualifications section has been removed (per Sam: that information is covered by the letters of recommendation).
- **Submission narrative** locked in per Sam's and William's review feedback:
  - Motivation: AM aerospace alloys → powder dosing as the manual bottleneck → unmet research-lab need (commercial dispensers expensive / mismatched, with a concrete Autotrickler-as-impractical bench-test note for the lower-cost end; open-source designs not rigorously tested for L-PBF) → the 30-powder, up-to-250 mL dispenser as the solution.
  - BYU Vertical Cloud Lab + Bayesian-optimization framing added in the introduction so the powder-doser need is grounded in the lab's self-driving-laboratory workflow.
  - AI–human collaboration motivation moved up into the Introduction and Objectives so the "engineer never opens a CAD GUI" framing is contextualized; the standalone "what we are not testing" paragraph and the topology-optimization aside have both been removed.
  - Methods anchored on GitHub Copilot agent mode w/ multiple models, **Bambu H2D for prototyping the dispenser**, future direct-printer-control, and prior pilot work giving agents access to scriptable CAD environments and component-selection tooling — described generically, with all internal issue references removed.
  - Hardware targets: 30 reservoirs, ≤250 mL/blend, **±1 mg per-powder accuracy with a ±0.1 mg stretch** (mg, not wt%), **cross-contamination tests on five to seven representative L-PBF feedstock powders** (no PSD-preservation requirement), inert-atmosphere enclosure deferred to v2. Hardware targets and timeline are now formatted as proper bulleted lists.
  - Validation/integration anchored on the **ultrasonic-atomization → L-PBF** pipeline using the BYU VCL's in-house ultrasonic atomizer.
  - Timeline: paper drafted and submitted at the end of the summer block; Fall 2026 / Winter 2027 reserved for the integration test, responding to paper reviews, and the v1.0 community release of the open-sou …[truncated]

### PR #29 [OPEN]: Add background research notes for powder dispensing and generative CAD
Background material to inform the BYU NASA Space Grant proposal (#26): a landscape + literature review for the two pillars the proposal hinges on — accurate multi-powder dosing for AM alloy discovery (#10) and generative CAD (#6).

### Source

Four parallel Edison Scientific `LITERATURE_HIGH` (paperqa-class) queries, plus one follow-up `LITERATURE_HIGH` query on LLM-CAD spatial-reasoning mitigations. Notes are kept verbatim so every claim retains its inline `(authorYYYY... pages X-Y)` citation key, with a numbered references section (DOIs + citation counts) at the bottom of each file for direct copying into `paper/rsc.bib`.

### Files added under `paper/background/`

- **`01-powder-dispensing-commercial-landscape.md`** — Mettler Toledo Quantos/CHRONECT, Chemspeed SWING/FLEX, Unchained Labs, Coperion K-Tron, Schenck, Gericke, Brabender, Movacolor, Freeman FT4, Sartorius. Quoted accuracy/throughput/price specs and a gap-analysis table. References #10. *(31.7k chars, 42 contexts.)*
- **`02-powder-dispensing-academic-literature.md`** — 2018–2025 peer-reviewed work on automated dosing, multi-material/HT metal AM (Ni, Ti, HEAs, refractory), graded-alloy discovery, self-driving labs, powder flowability. *(27.8k chars, 49 contexts, 30 DOIs.)*
- **`03-generative-cad-landscape.md`** — Fusion Generative Design, nTop, Siemens NX, Creo, ANSYS Discovery, Altair Inspire, Rhino+Grasshopper, plus code-CAD (CadQuery, OpenSCAD, build123d, FeatureScript, JSCAD) and AI/LLM-driven CAD. References #6. *(32.0k chars, 58 contexts, 14 DOIs.)*
- **`04-generative-cad-academic-literature.md`** — 2021–2025 peer-reviewed/arXiv work on generative CAD, LLM-CAD, programmatic CAD, learning-based shape generation; landmark datasets (DeepCAD, Fusion 360 Gallery, ABC, SketchGraphs, Text2CAD). *(31.1k chars, 63 contexts, 26 DOIs.)*
- **`05-llm-cad-spatial-reasoning-mitigation.md`** — synthesis triggered by review feedback on PR #35 (Claude Opus 4.7-generated CadQuery model). Catalogues the 10 PR #35 review failure modes (topological hallucination, wrong-direction Boolean cuts, doubled extrudes, dead/forgotten unions, arithmetic inconsistency, missing functional paths, vendor-envelope hallucination, ungrounded clearances, DfAM omission, broken doc cross-references) against the literature, and groups mitigations into (A) tool-side guardrails, (B) prompting/agent strategies, (C) representation choices, (D) human-in-the-loop, with a 6-item priority list for this repo and a manual-intervention stage table. §5 incorporates quantitative results from the follow-up Edison query (CADSmith ~38× Chamfer-distance reduction, CADCrafter 3.6% Invalid Rate, GenCAD-Self-Repairing 65.84% repair rate, CADReview's GPT-4o 41.5% error-detection ceiling, Sadik 2025's zero-Hausdorff result for code-level human edits) and reinforces two recommendations: an independent VLM "Judge" agent step (CADSmith-style) and ArtiCAD-style connector-first assembly prediction.
- **`06-tools-and-repositories-to-try.md`** — synthesis triggered by review feedback on this PR re-organising the references collected across `01`–`05` around what can actually be cloned, installed, or subscribed to today. Covers (i) code-CAD foundations (CadQuery, build123d, OCP, FreeCAD, ocp-vscode/cq-editor, PrusaSlicer/OrcaSlicer); (ii) 2024–2026 LLM-CAD research repos in two tiers — first-tier with verified GitHub URLs (CADSmith, CAD-Coder + GenCAD-Code, CAD-Recode, Text-to-CadQuery) and second-tier (DeepCAD, Text2CAD, GenCAD, CAD-MLLM, C …[truncated]

### PR #31 [OPEN]: Add brainstorming discussion of dispenser architecture options
- [x] §1 — relax 30 powders to loaded subset of ~8–12 (per @williamulbz)
- [x] §1 — add nuance: even pre-autonomy, value in back-to-back blends drawn from a larger pool (e.g. 30-choose-6); architectures with no path to grow beyond loaded subset lose points (per @sgbaird)
- [x] §1a — per-channel auger + solenoid + vibration stack, air-displacement and scraping out of scope (per @sgbaird)
- [x] §2.2 — physical layout description, footprint estimate, moving-cup variant
- [x] §2.2 — drop tunability bullet (applies to 2.3/2.4 too)
- [x] §2.2 — add link to new CAD visualization folder
- [x] §2.3 — soften cartridge-printability pitfall
- [x] §2.3 — emphasize shaft-engagement clutch as Will's "biggest area of interest" / single highest-leverage de-risking task
- [x] §2.4 — split pitfall by sub-variant; promote 1×N variant
- [x] §2.6 — pneumatic reclassified as out of scope
- [x] §3 — mass envelope (100–1000 g), A&D balance trade-offs, two-station option
- [x] §3 — drop unjustified 2.2 vibration-coupling distinction
- [x] §3 — electrical grounding of collection vessel (flexible, low-stiffness link)
- [x] §4 — add weighing-station design study to follow-ups
- [x] §4.1 — new "Synthesis of PR-thread feedback (Will + Sterling)" subsection that explicitly captures where the two reviewers agree, where they apply pressure in different places (Sterling → mechanism density at dispense site / weighing side; Will → cartridge/clutch-style designs), and the net implication for the ranking (per @swcharles); existing ranking content moved to §4.2
- [x] Clean up `powder-doser-transcript-2026-05-11.txt`: remove non-technical content (audio checks, screen-sharing logistics, greetings, filler), bridge run-on sentences, fix voice-to-text misspellings, preserve direct quotes
- [x] Add CAD visualization of §2.2 inward-pointing single-collection-point geometry under `design/cad/inward-collection-cup/`: 2D dimensioned matplotlib sketch (top + side), parametric CadQuery STEP model, and isometric + top-down line renders (per @sgbaird)

### PR #33 [OPEN]: Survey commercial powder-dosing equipment for quote gathering
The issue asks for quotes and clarifications on five commercial powder-dosing instruments (MTI AM-PD6, AM-PD16, PF-A; Labman MultiDose; METTLER TOLEDO Chronect XPR). The repo had no working area for that effort, so outbound asks would diverge per vendor and returned quotes would not be directly comparable.

### Changes

- **`docs/alternative-dosing/README.md`** — per-product survey: vendor link, format, capacity, resolution/accuracy, power, footprint, compliance, warranty, and indicative public pricing where available. Includes a comparison table across all five SKUs and an itemisation checklist (base unit, dosing heads, PC/balance, glovebox/anti-static, install + training, warranty, freight, lead time) so returned quotes line up.
- **`docs/alternative-dosing/quote-request-template.md`** — single reusable email template with bracketed placeholders; identical wording across vendors keeps quotes comparable.
- **`docs/alternative-dosing/quote-tracker.md`** — status table (request sent / quote received / lead time / notes) with the correct sales contact or form per vendor, and per-product asks (e.g. NRTL/CSA cost for MTI, glovebox build for Labman, RFID-head count for Chronect XPR). The issue's explicit "ask about lead time" call-out for **PF-A** is flagged here and in the survey.
- **`README.md`** — one-paragraph link to the new survey.

Pricing/quote PDFs are intentionally not committed; the tracker is the public surface and quote artefacts stay local.

### Notes for reviewers

- Specs and indicative prices were transcribed from each vendor's public product page on 2026-05-12; treat as a starting point and confirm at quote time.
- The Mettler product URL returned 406 to the fetcher; spec summary for Chronect XPR was cross-referenced from the Axel Semrau datasheet and DirectIndustry listing.
- The `Bal-APD6-S36` (MTI 6-channel + barcode, up to 36 compositions) is mentioned as an alternative to AM-PD16 worth pricing in the same RFQ — happy to drop it if out of scope.

### PR #35 [OPEN]: Add single-channel powder-doser module CAD (Idea B archetype) — v4 review-feedback redesign with Edison VLM-Judge loop
Executes the design half of #33: a self-contained single-channel module — auger + stepper + tap solenoid + vibration motor on one printable frame — that gets replicated `N` times around a shared collection cup to realize Idea B (`design/brainstorming.md` §2.2). Reuses the PR-#16 auger and PR-#25 actuator stack as-is.

### New folder: `design/cad/single-channel-module/`

- **`cad_model.py`** — parametric CadQuery assembly. Builds every printed part and places every vendor component, exporting `single_channel_module.step` plus per-printed-part STLs in `stl/` and four orthographic SVG/PNG renders in `renders/`.
- **`sketch_2d.py`** — matplotlib schematic. Constants are duplicated from `cad_model.py` and called out in the README so the two never drift.
- **`README.md`** — design rationale, BOM, print-orientation table, assembly order, fastener strategy, staged roadmap (`AI design → print → test → feedback`), parts-request list, Idea-C deferral note.
- **`edison_judge/`** — Edison Scientific VLM-Judge runner (`run_judge.py`) plus raw `roundN.task.json` + extracted `roundN.answer.md` artifacts for both judge passes.

### Top-level README

A new "Design" section links to this folder and to the `design/cad/inward-collection-cup/` visualization that ships with PR #31.

### v1 (commit c39e07f) — initial archetype

80 × 80 × 342 mm vertical frame built from `base_plate` + `top_plate` + 4× `corner_post` + `tap_collar` + `electronics_tray`. Stepper sat directly on top of the rotor via a flex coupler; the tap collar carried the JF-0530B and ERM with a 1 mm air gap to the rotor. 80 mm-square footprint with M4 corner bores on a 64 mm pitch sized to replicate around the §2.2 150 mm pitch circle.

### v2 (commit ed49e57) — review-feedback redesign

Substantial rework of v1 driven by [@williamulbz's PR review](https://github.com/vertical-cloud-lab/powder-doser/pull/35#pullrequestreview-4274628757). v1 is preserved in git history but is no longer documented in the README. v2 changes:

- **Single printed `spine`** (8 × 90 × 360 mm flat plate) replaces `base_plate` + `top_plate` + 4× `corner_post`. Everything else bolts to its +X face.
- **Bearing-coupled collar.** A 6805ZZ ball bearing (Ø25 / Ø37 / 7 mm) presses into the collar; the rotor presses into the bearing's inner race. Vibration & solenoid taps now actually couple to the rotor wall instead of dying in an air gap.
- **Plunger through-window.** A Ø5 hole through the collar body so the JF-0530B's plunger taps the rotor wall directly.
- **Integral collar features.** Mounting flange, gusseted solenoid wing, ERM pad and bolt-through bores are all one printed part.
- **Side-mounted NEMA 11 + 1:1 GT2 belt drive** (16T pulleys, ~110 mm closed-loop belt) frees the top of the rotor for powder loading.
- **Removable `cartridge`** (60-mm reservoir + 60° taper + 36-mm collar) snaps onto the rotor's PR-#16 v4 top loading slots; new dedicated powder-flow cross-section render walks reservoir → loading slots → helix → exit nozzle → cup.
- **Rotor protrudes 30 mm past the bottom of the frame** — the "base plate exit hole" is gone.
- **Adjustable-angle cradle** with M5 trunnion pivots and arc-slot detents at 0/15/30/45/60/75°.
- **M3 brass heat-set inserts everywhere**; per-joint fastener-strategy table in the README.
- **Refreshed PR-#25 envelopes** + new vendor parts (6805ZZ bearing, GT2 pulleys + belt) added to the assembly.

### v2.0a (commit 3308191) — copilot-reviewer housekeeping pass

Documentation/cleanup only …[truncated]

### PR #37 [OPEN]: Channel-sealing cap brainstorm + 3 parametric CAD prototypes
Issue #36 asks for descriptions and visuals of several sealing-cap concepts for a swappable powder-cartridge bottom (must seal the Ø3 mm exit during storage/handling, open inside the dispense head with at most "a small motor or linkage", and survive rotor + tap + ERM in dispense mode).

### `design/cap-brainstorming.md`
Six concepts, each scored against cap requirements **C1–C7** (seal at 0–90° tilt, survive rotor/tap/ERM, no-operator open/close, mechanism budget = "small motor", per-channel cost low, no shared seal surface, hobbyist FDM):

- §2.1 Twist shutter — two coaxial discs with sector slots; 60° throw open ↔ closed.
- §2.2 Spring-loaded auto-opening hatch — printed PETG flexure flap; **zero mechanism-side actuator** (a fixed cam pin pushes a tab on insertion).
- §2.3 Bayonet plug — quarter-turn male plug with 1.5 mm O-ring face seal; strongest seal of the three.
- §2.4–2.6 Sliding gate, silicone septum, magnetic plug — documented + explicitly **not** prototyped, with the failure-mode reasoning recorded so we don't re-litigate later (powder shear, axial-rotor redesign cost, ferrous-fines pickup respectively).

### Three CAD packages under `design/cad/sealing-cap-{twist-shutter,spring-hatch,bayonet-plug}/`
Each follows the established repo CAD-package convention (PR #31 / #33 / #35 layout):

- `cad_model.py` — parametric **CadQuery** model; targets the PR-#16 auger envelope (Ø25 OD, Ø3 exit) and includes a reference auger stub for visual sanity. Exports STEP + per-part STLs in `stl/`.
- `sketch_2d.py` — matplotlib dimensioned schematic. Constants are mirrored 1:1 from `cad_model.py`.
- `renders/` — iso / front / top / side SVG line renders + PNG rasterizations + the dimensioned schematic PNG.
- `README.md` — concept summary, file index, reproduction commands, C1–C7 mapping, bench-test plan, open questions.

Top-level `design/README.md` indexes the three packages, and `design/requests.md` lists the hardware (O-rings, micro-servos, torsion springs, printed reference cartridge) and three open questions the issue asked me to surface for human input before iterating.

```bash
cd design/cad/sealing-cap-twist-shutter   # or -spring-hatch / -bayonet-plug
pip install cadquery matplotlib cairosvg
python cad_model.py    # → .step + stl/*.stl + renders/*.svg
python sketch_2d.py    # → renders/*_sketch.png
```

All three packages reproduce cleanly from sources. Designs are intentionally agnostic to the in-flight single-channel module geometry (#34, PR #35) — the only assumed interface is the PR-#16 auger envelope, so this work doesn't block on those PRs landing.

### PR #41 [OPEN]: Add outreach contacts list for powder-dispensing collaborators
Compiles a single, citation-backed catalogue of people and organizations to contact for help with accurate, automated powder dispensing — drawn from the [accelerated-discovery thread #177](https://accelerated-discovery.org/t/accurate-powder-dispensing-for-chemistry-and-materials-science-applications/177), PR #29's background notes, and the rest of the repo (including commercial vendors like MTI).

### Changes

- **`docs/outreach/powder-dispensing-contacts.md`** — new living document with five sections:
  - **A. Individuals** — forum participants (Sterling Baird, @shijing, @kthchow, @loppe35, @muon, @mreish, Benji Maruyama / AFRL, Filippos Tourlomousis, Edward Mars / OpenTrickler, Adam MacLean / Autotrickler) and academic PIs (Vecchio + Charpagne / HT-READ at UCSD, Bahr, Neirinck, Cooper / PowderBot, Ceder / A-Lab, CMAC).
  - **B. Academic groups** — additional candidate PIs surfaced from PR #29's literature review (Mehta, Stein, Aspuru-Guzik, Abolhasani, Schrier).
  - **C. Commercial vendors** — Mettler-Toledo, Chemspeed, Unchained Labs, Hamilton, Thermo Fisher, Trajan, **MTI Corporation**, Coperion K-Tron, Schenck, Gericke, Brabender, Movacolor, Sartorius, Freeman FT4, A&D, CE Products, Autotrickler, INSSTEK, Emerald Cloud Lab — each with a "why relevant" and best contact route, ordered by relevance to the sub-\$10 k multi-powder metal-AM gap identified in PR #29.
  - **D. Open-source projects** — OpenTrickler, ARES OS, Acceleration Consortium, A-Lab, PowderBot, HT-READ.
  - **E. Suggested next actions** — four concrete steps (status update on AD #177, direct email to Vecchio/Charpagne, engineering intros with MTI/Chemspeed, follow-up issue after first replies).
- Every entry cites its source: `[AD #N]` for forum posts (so the post number is recoverable) and `[PR #29 — file]` for the Edison background notes, so the trail is auditable.
- **`README.md`** — adds a short "Outreach" section pointing to the new doc so it's discoverable from the repo landing page.

### Notes for reviewers

- Names of forum posters who used only a handle are kept as the handle; please confirm preferred contact channel before reaching out.
- The MTI Corporation entry was added per the issue's agent-instructions callout; it's positioned as a component supplier (feeders, hoppers, micro-augers) rather than a turnkey dosing platform.
- Intended as a living document — add entries with their source link as more candidates surface.

### PR #43 [OPEN]: Add generative-CAD outreach-contacts background note backed by Edison query
Resolves the request to identify named individuals and organizations the lab can contact for help with generative CAD, with verifiable public contact channels for each.

Follows the Edison-driven `paper/background/` pattern from #29 (see also #7, #27).

- **Runner — `paper/background/edison_run_outreach_contacts.py`.** Single `LITERATURE_HIGH` task with the prompt embedded verbatim. Prompt explicitly forbids fabricating emails and requires a public source URL per entry; covers 7 categories (academic CAD-LLM, code-CAD OSS, commercial CAD-API, SDL groups, AM experts, communities, funding).
- **Raw artifacts — `paper/background/edison_artifacts/gencad_outreach_contacts.{task.json,answer.md,references.md}`.** `status=success`, ~42 k-char answer, 11 references with DOIs.
- **Synthesis — `paper/background/06-generative-cad-outreach-contacts.md`.** ~45 named contacts organized into 7 categories with markdown subsections (### Name) for each entry, making each contact easy to link to directly. Quick-reference table at the top, then per-category subsections. Every entry ends with `(source: <full URL>)` pointing at the page where the listed channel (email / GitHub / X / lab page / Discord invite) can be verified. Where no public personal email exists (e.g., Faez Ahmed, Aspuru-Guzik, Nick Kallen), the entry says so and falls back to a lab/group/social channel rather than guessing.

Coverage highlights: DeepCAD (Wu, Zheng @ Columbia), Text-to-CadQuery (Xie, Ju @ ASU), CAD-Recode (Rukhovich, Aouada @ uni.lu), CADSmith (Barkley, Farimani @ CMU), ArtiCAD (Yu @ Beihang), SketchGraphs (Seff, Adams @ Princeton), Fusion 360 Gallery (Willis @ Autodesk), CAD-Coder / GenCAD (Doris, Ahmed @ MIT), Sadik @ Honda RI; CadQuery / build123d / OpenSCAD / FreeCAD maintainers; Zoo.dev/KittyCAD (Frazelle), McNeel (Baer), Plasticity (Kallen); Acceleration Consortium, Cooper, Cronin, Abolhasani, Schrier, Brown; Simpson, Beese, Pollock, Vecchio; CadQuery/build123d Discords, FreeCAD forum, IDETC-CIE, SCF, CAD'25; NSF DMREF / Future Manufacturing, ARPA-E DIFFERENTIATE, America Makes.

New files only — no overlap with #29's runner or `README.md`, so the two branches can land in either order without conflict. The synthesis README row in `paper/background/README.md` (introduced by #29) is intentionally not touched here; add it in a follow-up after #29 merges.

### PR #45 [OPEN]: Brainstorm: electrical & software architecture for design 2.2 (+ satellite-rev-a KiCad project)
Issue #44 asks for a brainstorming pass over the electrical/software design of the modular ("design 2.2") powder doser, given the per-channel actuator stack already chosen in #25 (Pi Zero 2 W + DRV8825/Tic T500 + DRV8871 + DRV2605L) and the `N parallel channels` concept from #31. It needs to cover the I/O fan-out story, simultaneous + independent per-channel control, easy module expansion, the load-cell feedback loop, and the still-open angle-control choice, with code samples.

### Changes

- **`design/electrical-software-brainstorming.md`** — new doc, structured like the existing `design/brainstorming.md`:
  - **§2 I/O fan-out table** quantifying where the Pi Zero 2 W runs out of headroom as N grows (GPIOs, hardware PWMs, single I²C bus, the DRV2605L 0x5A address collision that forces a mux or satellite, USB host port, Linux jitter on step/servo PWM).
  - **§2b Angle-control sub-problem** comparing hobby servo vs NEMA + lead-screw vs linear actuator; argues the choice is topology-independent and should be deferred until a single channel is bench-tested.
  - **§3 Three candidate topologies**, each with a Mermaid block diagram, per-module wiring, simultaneity story, add-a-module workflow, BOM/$/channel, and failure-isolation analysis:
    - 3.1 Pi-direct fan-out (TCA9548A + PCA9685 + Tic T500 over USB hub)
    - 3.2 CAN-bus satellite MCUs (per-module RP2040 + TMC2209 + DRV8871 + DRV2605L)
    - 3.3 USB-CDC satellite MCUs **(recommended)** — same satellite stack, USB enumeration replaces CAN and gives plug-and-play discovery
  - **§3.4 Satellite PCB outline (topology C)** — added in response to PR feedback. 50 × 50 mm 2-layer FR-4 board, mechanical interface to the NEMA 11 bracket from #25, three edge connectors (USB-C, 12 V screw terminal, JST-XH stepper) plus on-board JST-PH headers for solenoid + ERM and a 3-pin servo header, a Mermaid block diagram of the board, an RP2040 pin-assignment table that matches the §6 firmware sketch, component-placement notes (incl. *why* each satellite carrying its own DRV2605L on a local I²C bus resolves the 0x5A address-collision problem), per-board BOM estimate (~$15–25), and an incremental bring-up order. Now cross-links to the committed KiCad project at `hardware/kicad/satellite-rev-a/`.
  - **§3.5 PCB design software available in this environment** — added in response to PR feedback. Surveys what is actually installable in the agent sandbox: **KiCad 7** (`7.0.11+dfsg-1build4` from `noble/universe`) is recommended to match the existing `hardware/kicad/` convention from #25 and works headlessly via `kicad-cli sch/pcb export`. Also catalogues Horizon EDA (apt), LibrePCB (AppImage), pcb-rnd (apt, layout-only), and KiCanvas (browser viewer for `.kicad_sch` PR diffs), with a copy-pasteable `kicad-cli pcb export svg` invocation that this PR now uses to render the Rev A artifacts.
  - **§4 Load cell** (NAU7802 vs HX711, Pi-direct vs scale-satellite) with a soft-trim PID skeleton (bulk → slowdown → final-grain).
  - **§5 Concurrency** — `asyncio.gather()` blend orchestrator showing parallel per-channel control off a single Pi process.
  - **§6 Satellite firmware sketch** (MicroPython on RP2040, PIO-driven step train, hardware PWM tap+servo, dedicated local I²C eliminates the DRV2605L address collision).
  - **§7 Discovery / hot-add** per topology, with a `pyudev`-style auto-registration loop for 3.3.
  - **§9 Open questions** punted to follow-ups (TMC2209 vs DRV8825 revisit, ADC choice, inert-atmosphere feed …[truncated]

### PR #47 [OPEN]: Add parametric auger bracket CAD (split shaft-collar) sized for the 25 mm Archimedes auger, with baseplate clearance for the PR #49 geared auger
First part of the part-by-part Powder Doser build: a split shaft-collar bracket on a rectangular mounting flange that holds the auger so it can spin freely while staying constrained. Print x2.

Sized to match the **Archimedes auger from PR #16** (`cad/auger/archimedes-auger.scad`: `outer_diameter = 25 mm`, `total_height = 250 mm`, M3 spindle mount on top), and lifted to clear the **Ø50 mm gear** of the geared variant from **PR #49** when the bracket is mounted on the chassis baseplate.

New self-contained CAD module at `design/cad/auger-bracket/`:

- **`cad_model.py`** — parametric CadQuery model; all dimensions are named constants at the top for easy retuning. Exports both STEP and STL.
- **`stl/auger_bracket.stl`** — ready-to-print binary STL.
- **`auger_bracket.step`** — STEP for editing in any CAD package.
- **`render_views.py` / `render_assembly.py`** — headless VTK renders (iso/front/top/side + a two-bracket-on-shaft assembly diagram) committed under `renders/`.
- **`README.md`** — geometry, parameters, fits, print orientation; cross-references PR #16 and PR #49.

Design choices keyed to the drawing callouts:

- Bore Ø **25.5 mm** = 25 mm auger OD + **0.5 mm diametral clearance** — free-running fit on FDM, with margin for elephant-foot squish on the bore wall.
- Collar OD **33.5 mm** (4 mm wall around the bore).
- **2 mm slot** continues from between the top ears, through the collar wall, into the bore — single M3 screw across the ears pinches the halves onto the shaft.
- Mounting plate **60 × 12 × 14 mm**, sized so the 33.5 mm collar OD fits with comfortable margin to each corner M3 mounting hole. The plate is **14 mm thick** (was 4 mm) — the extra 10 mm of material on the bottom face lifts the bore axis to Z = 29.25 mm above the bottom, giving **4.25 mm of radial clearance** between the PR #49 geared auger's Ø50 mm gear OD (`gear_tip_r = 25 mm`) and the chassis baseplate. All collar / tab / fillet / clamp-screw geometry is keyed to `COLLAR_CENTRE_Z` / `COLLAR_TOP_Z`, so it auto-translates with the lift; the corner mount holes still pass straight through to the bottom face.
- **3 mm fillet** at the collar/plate intersection per the "smooth transition" callout. Fillet edge selector computes the true geometric intersection X (`sqrt(R² − dz²)`) so it works for any retuned `AUGER_OD` / `COLLAR_WALL` / `PLATE_THICKNESS`.
- Clamp ears are **integrally joined** to the collar body — sunk into the collar by `TAB_COLLAR_OVERLAP=6 mm` and blended with `FILLET_TAB_COLLAR=1 mm` so they grow continuously out of the collar wall instead of sitting on top of it (PR review feedback).
- Clamp ears are **slim along the screw axis** (`TOP_TAB_W=3 mm`) so the M3 tightening screw is short and goes through ~8 mm of material instead of 14 mm. `TOP_TAB_H=7 mm` gives the Ø3.4 clamp hole — positioned at `COLLAR_TOP_Z + TOP_TAB_H/2` — proper centering between the top of the collar circle and the top of the part, with ~1.8 mm of wall above and below it (PR review v2 feedback).
- Four M3 corner mounting holes through the plate.
- Plate face down on the bed per the "print on this face" callout — bore axis ends up parallel to the bed, no internal supports.
- Assembly render: `BRACKET_SPACING = 180 mm` centre-to-centre along the 250 mm auger.

A defensive `assert` checks that the tab footprint stays within the collar OD so future parameter retunes can't silently produce an un-fillet-able geometry.

```python
# design/cad/auger-bracket/cad_model.py — top-of-file k …[truncated]

### PR #49 [OPEN]: Geared Archimedes auger + NEMA 11 pinion (cad/auger-geared/) — full-length, short alternate, and per-nozzle test variants
Geared sibling of `cad/auger/archimedes-auger.scad` (PR #16): an Archimedean auger with an external spur-gear band that meshes with a 16-tooth pinion on a NEMA 11 stepper. Ships in two length variants that share all internal geometry, plus four short gearless test pieces — one per nozzle design.

## v2 — addressing PR review (comment 4460165741)

- Identified root cause of the "solid gear" issue: `spur_gear_2d` rendered the auger band as a `circle(r=root_r)` solid disc, which sealed the bore at the band's z and made the auger a closed cup.
- Identified NEMA 11 / auger collision: `C = 21 mm` < `12.5 mm` auger OR + `14.1 mm` motor half-body (5.6 mm overlap).
- Made `spur_gear_2d` accept an `inner_r` so the auger gear band is **annular** (bore stays open through the gear); the pinion stays solid (default `inner_r = 0`).
- Resized the mesh so the NEMA 11 body clears the auger:
  - new pair `Z_p = 16 / Z_g = 48`, `m = 1.0` → `C = 32.0 mm`, ratio **3.0 : 1** (was 2.5 : 1)
  - 5.4 mm radial air gap between the auger OD and the nearest face of the NEMA 11 frame
- Added `assembly-preview.scad` + STL + iso/top/front PNGs showing the auger + pinion + NEMA 11 dummy body in their final relative positions, with the radial clearance visible.

## v3 — addressing @williamulbz review (comment 4461555396)

- **Restored the inner Archimedean screw.** v1/v2 copied PR #16's v5 verbatim, but v5 had explicitly stripped the central shaft + helical fin after a single H2D print test produced inner-core stringing — leaving the geared auger as an empty tube. v3 puts the geometry back, matching PR #16's v4.1-era inner design that printed successfully:
  - Central shaft Ø8 mm, fuses tangentially to the funnel cone wall at z ≈ 3.5 mm (no floating tip, does not block the 1.5 mm exit hole).
  - Helical fin: 10 mm pitch, 2 mm thick, single `linear_extrude` with proportional twist → **continuous** from funnel mouth to top cap underside, no break at the gear band z. Manifold sinks of 0.4 mm into the shaft and 0.2 mm into the wall.
  - Confirmed before push with two cross-section renders (`archimedes-auger-geared-cross-section.png` and `archimedes-auger-geared-short-cross-section.png`) — both show the helix turn-by-turn through the gear band region. STL facet counts: full 38,940 / short 29,086 vs ~1,235 in v2 (~30× increase = the helix sweep).
- **Added a short alternate variant** as `archimedes-auger-geared-short.scad` / `.stl`. `total_height` 250 → 180 mm (-70 mm = -7 cm), with the trim taken entirely from the body **above** the gear band. Gear-to-dispensing-end distance preserved at 83.33 mm so the same pinion + motor bracket fit the alternate unchanged. Capacity ≈ 56 cm³ vs ≈ 80 cm³ for the full-length variant.
- **Refactored.** Shared geometry now lives in `auger-core.scad` (parametric `archimedes_auger_geared(total_h, gear_center_z)` + all submodules and constants). Both top-level `.scad` files just set parameters and call the assembly module, so the two variants cannot drift apart.
- Migrated `mesh-preview.scad` and `assembly-preview.scad` to the new parametric API; added `assembly-preview-short.scad` showing the alternate variant in the same view.
- Updated README with the v3 section, helix parameters, alternate-variant section, an expanded internal-geometry guarantee (now including a helix-presence check item), and a refreshed "Reproducing the renders" block.

## Edison Scientific literature review — addressing @sgbaird (comment 4546247154)

- Added `cad/auger-gear …[truncated]

### PR #51 [OPEN]: Add parametric tap-collar CAD (split mount plate + collar with motor/solenoid mounts)
CAD for the *Tap Collar* — an independent split-collar that wraps the auger to carry a coin vibration motor and a push/pull solenoid, with a chassis-mounted hardstop that prevents wire wind-up by stopping the collar from rotating with the auger.

New self-contained module at `design/cad/tap-collar/` with two independently-printed parts whose shared dimensions (bore Ø25.5, collar OD Ø33.5, 2 mm clamp slot, 60 × 18 × 14 mm plate, M3 hardware) are kept in lock-step with the bracket from PR #47 so they reuse the same hardware and the same Ø25 mm Archimedes auger from PR #16.

### Parts

- **`mount_plate`** — bracket-style plate footprint and 4-corner M3 hole pattern, circular collar replaced by a small **hardstop bump** on the +X end of the plate top. The bump's top face sits 0.25 mm below the bottom face of the resting lower clamp tab, so the tab rests on the bump (the *contact point* from the drawing) and rotation is arrested with the tabs horizontal. The bump sits entirely below the lower-tab Z range so it does not interfere with the collar or with installing it onto the auger. The +X corner M3 mount hole punches straight through the bump body (the "hollow" option), so the bump can be wide and structurally robust while still letting the screwdriver through. The +X corner hole is **countersunk** (M3 90° flat-head, Ø6 × 1.30 mm) into the bump top so the screw head sits flush with the bump's top face and the contact face stays flat against the resting lower clamp tab. The plate top also carries a half-cylindrical **collar relief** (axis along Y, R = COLLAR_OD/2 + 0.25 = 17.00 mm) cut through the full plate Y-extent, giving the collar a 0.5 mm diametral free-running fit over the plate — the same tolerance the bracket bore uses on the auger in PR #46 / #47 — so the collar can spin freely above the plate instead of physically intersecting it. The plate's Y-extent (`PLATE_DEPTH` = **18 mm**) is matched to `TC_COLLAR_DEPTH` (v4 print feedback from Will) so the mounting plate is the same width as the tap collar along the auger axis; an `assert PLATE_DEPTH == TC_COLLAR_DEPTH` locks the two together.
- **`tap_collar`** — split shaft-collar reusing the bracket's bore / OD / clamp slot / clamp-screw geometry, with the slot rotated 90° so the two clamp ears face +X and the lower ear is the hardstop contact. Clamp ears widened from 3 → 8 mm along X. The collar is **lengthened along the auger axis to 18 mm** (`TC_COLLAR_DEPTH`, vs 12 mm on the bracket) so the full solenoid mounting boss sits over solid collar material and the M2 mount holes are no longer cantilevered into mid-air. Clamp screw is intended to set the running fit, not lock the collar to the shaft.
- **Coin motor mount** (−X side of the collar): **rectangular reinforced slab** (14 mm wide × full 18 mm collar length × ~4 mm thick) that sinks `PAD_COLLAR_OVERLAP` = 3 mm into the collar OD, with the slab/cylinder intersection blended by a 1.5 mm fillet — same template the bracket uses for its plate ↔ collar reinforcement in PR #47. Carries a Ø10 × 1 mm adhesive recess for a Ø10 coin vibration motor.
- **Solenoid mount** (+Z top of the collar): **rectangular reinforced slab** (same template as the coin pad, 14 mm × 18 mm × 5 mm, 3 mm overlap into the collar OD, 1.5 mm fillet at the intersection) with two M2 holes at 12 mm pitch flanking a Ø6 plunger clearance hole that goes straight through the collar wall so the plunger taps the auger directly. Defensive `assert`s catch retunes that would let  …[truncated]

### PR #53 [OPEN]: Add parametric auger clamp bracket (CAD + 3D-print artifacts)
Models the split shaft-collar-with-mounting-plate bracket sketched in the issue, sized to clamp the v5 Archimedes auger from #16 (OD = 25 mm) with print-friendly tolerance, and ships ready-to-slice artifacts.

The whole part is **one piece**, generated as a single 2D profile (ring + ears + slit + tangent flank transitions + plate) in the XZ plane, then `linear_extrude`'d uniformly along the auger axis for the full 10 mm width. This keeps the bracket flat-flanked and constant-depth — matching the hand sketch — with no 3D pyramidal/frustum blends.

### Geometry (per the sketch)
- Bore Ø 25.8 mm (auger OD + 0.8 mm diametral clearance)
- 4 mm ring wall, 10 mm width along the auger axis
- 2 mm clamp slit at top with twin ears + horizontal M3 through-hole for the pinch bolt
- Tangent "smooth transition" flanks from the lower ring OD down to the plate top, generated by a 2D `hull()` of the lower half-disc and the plate rectangle (extruded uniformly — single piece, no pyramidal base)
- 50 × 4 mm mounting plate with two M3 mounting holes 38 mm apart; flat bottom face is the print-on face

### Files added under `cad/auger-bracket/`
- `auger-bracket.scad` — single parametric OpenSCAD source; all dimensions named at top
- `auger-bracket.stl` — binary STL, ready to slice; CGAL `Simple: yes` / `Volumes: 2`, `trimesh.is_watertight: True`, bbox 50 × 10 × 41.75 mm
- `views/{iso,front,top,side}.png` — 600 × 600 OpenSCAD renders
- `README.md` — dimensions table + reproduction steps + print settings

### PR #55 [OPEN]: Add CADsmith-style auger bracket (split shaft collar + mounting flange)
Design a 3D-print-ready bracket that clamps around the 25 mm OD Archimedes auger from PR #16, modeled as a split shaft collar with a filleted mounting flange. Two brackets support the auger near its ends, leaving the centre span clear for the planned solenoid (#25) and coin-vibration motor (#31).

The bracket was authored as a parametric CadQuery script. CADsmith (https://github.com/vertical-cloud-lab/CADSmith) is a CadQuery-based pipeline that requires `ANTHROPIC_API_KEY`, which is not provisioned in the Copilot Coding Agent sandbox (only `ZOO_API_TOKEN` and `EDISON_API_KEY` are), so the part was hand-authored in the same CadQuery shape CADsmith's Coder agent would emit — it can be fed back through the CADsmith loop for validation/refinement later without restructuring.

### Design (matches the hand sketch in the source issue)

| feature | dimension | note |
| --- | --- | --- |
| bore Ø | 25.4 mm | PR #16 auger OD 25 mm + 0.4 mm dia. slip-fit |
| ring wall (radial) | 5 mm | bears the M3 clamp load |
| ring axial width | 15 mm | bearing surface along the auger |
| clamp slit | 2 mm | "2mm" callout — top-down through both ears + ring wall to the bore |
| ears (each) | 8 × 8 × 10 mm | M3 clamp screw across both ears |
| M3 clamp screw | Ø 3.2 mm clearance | tightening pinches the ring onto the au

### PR #57 [OPEN]: Mounting plate + hinged baseplate built around real upstream parts, aligned to issue #62 drawing (front-face NEMA-11 mount, centred auger, sandwich side hinges, full-width front ramps, open auger gap)
- [x] Imported real upstream parts (auger #49, bracket #47, tap-collar #51)
- [x] Centred auger, symmetric plate, equal/thick hinges, no plinths, no underside features
- [x] Lifted brackets so gear band clears plate top with no slot
- [x] Packed bracket / tap-collar / gear-band with ~1 mm clearance
- [x] NEMA-11 pinion centred on gear band in Y
- [x] 3-layer sandwich side hinges spanning full ramp width
- [x] **Removed obsolete linear-actuator base clevis from baseplate** (was leftover from old design)
- [x] **Extended baseplate hinge arms back onto the baseplate top** (40 mm overlap) so the arm bottom face is in complete contact with the baseplate — no cantilever
- [x] Updated KCL mirror, render_assembly.py (drop actuator line/length annotation, extend arm side projection), and README

### PR #59 [OPEN]: Hinged mounting plate + baseplate assembly with linear-actuator tilt (CADsmith-authored)
Designs the foundation that ties together the auger, brackets, tap collar, NEMA-17, cup and scale from #46/#48/#50, with a hinge co-axial with the auger discharge bore so the head can tilt 0°→90° driven by a linear actuator without cutting the auger or blocking powder flow.

> **CADsmith now runs.** With `ANTHROPIC_API_KEY` provisioned, both printable plates were driven through [CADsmith](https://github.com/vertical-cloud-lab/CADSmith)'s multi-agent pipeline via `run_cadsmith.py` — **both converged on iteration 0**:
> - mounting plate: 3 LLM calls, 67 s, 250×80×29.5 mm, vol Δ 1.1 % vs hand-authored
> - baseplate: 3 LLM calls, 45 s, 300×200×206 mm, vol Δ 0.5 % vs hand-authored
>
> CADsmith STEPs are copied alongside the hand versions at `step/{mounting_plate,baseplate}.cadsmith.step`; Judge three-view renders, generated CadQuery scripts, and full logs are committed under `cadsmith_runs/`. Two small upstream patches were needed (`max_tokens` 4096→16000, walk all `"text"` blocks instead of `content[0].text`, and swap the Judge's retired `claude-opus-4-20250514` pin for `claude-opus-4-5`) — written up in the README's pros/cons section. The hand-authored CadQuery is kept as the assembly source of truth since CADsmith is single-part-oriented and doesn't emit the tilted multi-part assembly.

### New package: `design/cad/mounting-plate-assembly/`

- **`cad_model.py`** — parametric CadQuery, all dimensions as top-level constants:
  - `mounting_plate` (250×80×5): hole groups for 2× brackets + tap-collar + NEMA-17 (M3, with Ø22 pilot), hinge pillars hanging *outside* the auger barrel, and an LA tab placed close to the hinge to keep stroke ≈ 67 mm.
  - `baseplate` (300×200×6 on four 150 mm legs): mating hinge pillars, LA base clevis, discharge cut-out aligned with the bore.
  - Placeholder solids (auger, bracket, tap-collar mount, NEMA-17, linear actuator, cup, scale) used only in the assembly STEP.
  - Tilt is applied about **−Y** so the motor end swings *up*; the naive `+Y` rotation collides the NEMA-17 with the baseplate at 90°.
- **`run_cadsmith.py`** — drives CADsmith's Planner→Coder→Executor→Judge loop on the two printable plates from precise dimensional prompts; copies the converged STEPs to `step/*.cadsmith.step` and writes a `cadsmith_runs/summary.json`.
- **`step/` + `stl/`** — every printable part (hand-authored), CADsmith variants of both plates, plus `assembly_{0,45,90}deg.step`.
- **`cadsmith_runs/`** — per-part CADsmith iter-0 STEP/STL/Judge-render/CadQuery-script/log, plus a top-level summary.
- **`render_views.py`** — VTK iso/front/top/side PNGs into `renders/` (run under `xvfb-run`; uses `Shape.toVtkPolyData` since `cadquery.occ_impl.assembly.toVtkPolyData` is gone in 2.7).
- **`diagrams.py`** → `diagrams/`: install diagrams for both plates with every M3/M5 hole labelled (`D1–D4`, `T1–T4`, `M1–M4`, `NEMA-1..4`, hinge, LA tab); `rotation_0_45_90` side-elevations with computed LA length per tilt (~77 / ~100 / ~144 mm); `powder_flow` showing auger → discharge bore → plate notch → baseplate cut-out → cup.
- **`README.md`** — hardware list, print orientation, reproduction commands (including the CADsmith path), and empirical CADsmith pros/cons from the actual run.

### Key geometric invariant

Hinge axis = auger discharge axis, which is *also* the powder-exit point. This is the only configuration that lets the head tilt without (a) cutting through the auger barrel, (b) moving the dispensing point relative to the cup, or (c) requiring a …[truncated]

### PR #61 [OPEN]: Add single-Pico-W test-module electronics: KiCad schematic, MicroPython firmware, and wiring docs
Bench rig that exercises one powder-doser module (auger rotation, tapping, vibration, dispensing angle) from a single Raspberry Pi Pico W, reusing the parts identified in #25 but dropping the Pi Zero 2 W / Perma-Proto Bonnet so the whole module can be driven over USB-serial without a Linux stack. The design only uses GP0..GP15 so the same firmware runs unmodified on a plain Pico as well.

### Hardware (`hardware/test-module/`)

- **KiCad 7 project** under `kicad/`, emitted by `generate.py`:
  - Project-local `test_module.kicad_sym` for the breakouts that aren't in stock symbol libs (Pi Pico W, DRV2605L, DRV8871, DRV8825, D24V22F5, Pololu #3776 shunt regulator, ERM, JF-0530B solenoid, 4-wire NEMA-11, hobby servo, barrel jack).
  - The `DRV8825_Carrier` symbol matches the physical 2×8 (16-pin) header on the Pololu #2133 carrier — left side `nEN, M0, M1, M2, nRST, nSLP, STEP, DIR`; right side `VMOT, GND, B2, B1, A1, A2, nFAULT, GND`. There is no separate `VDD` pin: the carrier's logic supply is generated on-chip from `VMOT` by the DRV8825's internal 3.3 V LDO, so the Pico W's 3.3 V GPIOs drive the logic inputs directly.
  - Schematic uses global-label-only connectivity (no routed wires) with short stubs so labels read clearly. `SYMBOL_PINS` offsets are expressed in schematic page coordinates (Y+down) — the opposite sign of the symbol-editor pin definitions — so global labels render aligned to the actual pin rows on every component.
  - `kicad-cli` exports SVG / PDF / PNG headlessly; renders committed.
- **`README.md`** — subset BOM (~$45 + PSU + stepper + breadboard on top of a Pico W), full assembly order with the DRV8825 `V_REF` cal step, `nSLP`/`nRST` tie-up, 100 µF on `VMOT`, the Pololu #3776 shunt regulator (SR1) wired across +12V/GND beside U5 to clamp stepper back-EMF below the DRV8825's 45 V absolute max (with a "Why the shunt regulator is on the bench rig" rationale section), a "Why the Tic T500 USB stepper controller from PR #25 is *not* on the bench rig" section (the Pico W already provides USB-serial control and STEP/DIR/microstep generation in firmware, so a Tic T500 would be a redundant second MCU in the chain — the production system can still adopt it later without firmware changes), and a complete pin/net table that is the contract between schematic and firmware.

### Firmware (`hardware/test-module/firmware/`, MicroPython on RP2040 / Pico W, edited via VS Code + MicroPico)

The firmware targets **MicroPython 1.22+** on the Pico W and is developed in VS Code using the **MicroPico** extension (`paulober.pico-w-go`), which handles project upload and provides the built-in terminal that streams stdout *and* feeds keystrokes into `sys.stdin` — that's all the keyboard-driven scripts need.

- **`config.py`** — every tunable in one file: pin map, microstepping, RPM, dispense angle, DRV2605L effect ID / library / duration, tap count + on/off ms + PWM duty, servo pulse calibration, smooth-motion parameters (`SERVO_SPEED_DEG_PER_S`, `SERVO_UPDATE_HZ`), and named presets. Edit, re-upload via `MicroPico: Upload project to Pico`, soft-reset, done.
- **`main.py`** — MicroPython's boot entrypoint. `Stepper` / `Vibration` / `Tap` / `Servo` driver classes (built on `machine.Pin` / `machine.PWM` / `machine.I2C`) + a non-blocking USB-serial REPL using `uselect.poll(sys.stdin)`. The `Servo` class interpolates from the current angle to the target at `SERVO_SPEED_DEG_PER_S` deg/s (default 60 deg/s, 50 Hz update) so `a`/`p` commands ramp smoothly  …[truncated]

### PR #63 [OPEN]: Mounting plate + baseplate with offset hinge (issue #62)
Adds the foundation parts the rest of the doser bolts onto: a rotating **mounting plate**, a bench-side **baseplate**, and an M5 **hinge pin**. The plate hinges 0–90° about its +Y edge so at 90° the auger points straight down through a powder window in the baseplate.

### `cad/mounting-plate/`

- **`cad_model.py`** — single parametric CadQuery source of truth. Upstream bolt patterns (PR #49 NEMA-11, #51 tap-collar, #55 bracket) are reproduced at design coordinates so those parts drop in unmodified.
- **Mounting plate** — 110 × 220 × 6 mm. 2× bracket holes at Y = ±95, tap-collar at Y = +75 (hinge side, per sketch), integrated NEMA-11 boss at X = +32 (gear C = 32) with Ø22 pilot + 4× M3 @ 23 pitch, gear-band clearance window, 2 triangular hinge knuckles dropping 18 mm below the plate plane to Ø12 eyes.
- **Baseplate** — 150 × 328.7 × 6 mm. 2 upright posts (28 mm) interleaving the knuckles, 50 × 50 mm powder window centred where the dispense tip lands at 90° tilt (Y = +153.7), 4× M5 corner bolt holes.
- **Hinge** — offset design: knuckle eye 18 mm below plate underside, post 28 mm above baseplate top → 10 mm working air gap at 0°, no collision sweeping to 90°.
- **Exports** — `step/` and `stl/` per part; `views/` four-view PNGs; `assembly/` iso renders at 0°/45°/90° + ortho views of 0° with placeholder auger/bracket/tap-collar/motor/pinion sized from upstream PRs.
- **`engineering_drawing.{png,pdf,svg}`** — 4-panel dimensioned drawing (mounting-plate top + side, baseplate top, hinge detail) generated by `engineering_drawing.py` from the same constants as the model.

### Geometry summary

| | Value |
| --- | --- |
| Plate / base footprint | 110 × 220 × 6 / 150 × 328.7 × 6 mm |
| Auger ↑ from plate top | 19.73 mm |
| Hinge axis (Y, Z) | (+110, −24) mm |
| Knuckle drop / post H | 18 / 28 mm |
| Knuckle X pitch | 60 mm |
| Bracket Y pitch | 190 mm |
| Dispense @ 0° → 90° | (+125, +19.7) → (+153.7, −39) mm |

### Open question

Plate is cantilevered at 0° (supported only at the hinge edge). Fine for the ~1 kg load on 6 mm PLA; happy to add a fold-out rest leg under the motor end if preferred.

### PR #66 [OPEN]: Servo-driven mounting plate hinge — involute gear band + supported MG996R mount
Implements the servo-driven mounting-plate hinge (issue #63) on top of PR #57 geometry.

## Mechanism

- **Hinge gear (mounting plate)** — the +X outer mounting-plate hinge lobe is extended into a 40-tooth m ≈ 0.908 spur gear band (PCD 36.3, tip Ø 38.2, face width = lobe thickness ≈ 12.30 mm), integrated into the mounting plate as a single solid.
- **Servo pinion** — new part `servo_pinion.{step,stl}`: 20-tooth m ≈ 0.908 spur pinion (PCD 18.2, tip Ø 20.2), Ø 6 + chordal-flat bore for the MG996R 25-T spline, giving a **2 : 1 reduction at C = 27.25 mm**. The module is back-solved from C and the tooth counts so the 40 T hinge gear at the auger axis (Z = +29.25) meshes exactly with the 20 T pinion at the required Z (= +2.0, i.e. 10 mm above the baseplate top — the centreline of the MG996R's 20 mm-thick body, per the dimensioned drawing).
- **True involute tooth profile** for both the hinge gear band and the pinion (12-point base-circle involute per flank + 3-point tip arc), matching PR #49's `spur_gear_2d` (`cad/auger-geared/gear-teeth.scad`). Replaces the earlier straight-flank trapezoidal approximation.

## Servo mount (baseplate)

- Vertical wall on the baseplate top at X = +55 mm. **MG996R dimensions are driven by the dimensioned drawing Will posted on the PR** (body 40 × 20 × 36.8 mm, flange tip-to-tip 54.5 mm, flange thickness 2 mm, spline 10.1 mm from the near body end). Servo body sits at X ∈ [+59, +95.8] mm, entirely outboard of the mounting plate.
- **Spline axis Z** — placed at **+10 mm above the baseplate top** (driven directly from `PINION_Z_ABOVE_BASE_TOP = 10.0` in `cad_model.py`), matching the centreline of the 20 mm-thick MG996R body where it seats against the wall. Was previously 7.25 mm.
- **Mounting holes**: 4 × **Ø 5** on a **49.5 × 10 mm** rectangular pattern, with hole-centre Y offsets from the spline axis of **−14.85 mm** and **+34.65 mm** (both annotated directly on the drawing). With the spline axis raised to +10 mm above the baseplate top, the lower hole pair sits at +5 mm and the upper pair at +15 mm above the baseplate top.
- **Servo-head hole**: **Ø 10 through** the wall + a **Ø 14 × 1.5 mm counter-bore** on the servo side so the MG996R output collar tucks into the wall and the flange seats flat against it.
- The wall is **structurally tied to the baseplate** by (a) a forward baseplate-thickness *porch* under the full servo footprint so the MG996R body is not cantilevered off the baseplate front edge, and (b) a 22 mm triangular gusset on the back face of the wall that ties the wall top back into the baseplate top. Together they carry the servo weight and reaction torque.
- A small pinion-swing clearance pocket is cut through the baseplate front edge under the pinion footprint.

## Interference fixes

- The baseplate's middle-third hinge arms used to pierce the mounting-plate body at 0° fold-down (5904 mm³ of overlap). Fix: two vertical clearance slots cut through the plate (one per arm) at Y ∈ [+73, +117], with X-bands matching the arm spans ±0.5 mm clearance, so the arms pass cleanly through when folded.
- The baseplate hinge-arm back (−Y, motor-facing) face is no longer rectangular. It is replaced with a ~58°-from-horizontal slope running from Y = +75 at the baseplate top up to Y = +91 at the hinge-axis level, giving the mounting plate's underside clearance to sweep through 45° and beyond.

## Validation

`validate_no_interference()` in `cad_model.py` is called from `main()` and prints OK/FAIL per check:

- ` …[truncated]

### PR #68 [OPEN]: Fix geared auger exit path: taper central shaft through the funnel and extend helical fin to the exit hole
- [x] Open the path under the shaft (`auger-core.scad`)
- [x] Locate the exit hole within the flight sweep
- [x] Extend the helical fin to the new floor
- [x] Re-render full + short STLs and PNG previews
- [x] **(v3.1)** Widen funnel-region gap: shaft tapers Ø8 → Ø1 from top of funnel down to exit hole
- [x] **(v3.2)** Extend the helical fin down through the funnel region, tapering with both the shaft and the funnel cone wall
- [x] **(v3.3, addressing comment 4330645601)** Fix screw phase mismatch at the seam — `linear_extrude(twist)` follows the left-hand rule and `rotate([0,0,θ])` follows the right-hand rule, so the pre-rotation needed is `-funnel_twist`, not `funnel_twist`. Helix is now truly continuous in phase across z = `bottom_cap_h`. Added a top-down isometric cross-section at the taper start (`archimedes-auger-geared-funnel-top.png`).

### PR #70 [OPEN]: Assess OCP CAD Viewer VS Code extension for CadQuery
Issue asked to evaluate the [`bernhard-42.ocp-cad-viewer`](https://marketplace.visualstudio.com/items?itemName=bernhard-42.ocp-cad-viewer) VS Code extension as a tighter feedback loop than Onshape for the repo's CadQuery work, and how it compares to [CQ-editor](https://github.com/CadQuery/CQ-editor).

### Changes
- **`docs/tooling/ocp-cad-viewer.md`** (new) — written assessment:
  - **Recommendation:** adopt as the default local authoring loop for CadQuery/build123d; keep Onshape for shareable review, CQ-editor as a fallback.
  - **Fit with repo:** consumes the same `cq.Workplane` / `cq.Assembly` the existing `cad/<part-name>/<part-name>.py` scripts already build; committed STEP/STL and the headless `render_views.py` / `cad/meta-tools/render_step.py` PNG pipeline are untouched. Only adds `ocp-vscode` as a dev-only pip dep.
  - **Comparison table** vs Onshape and CQ-editor (feedback loop, diff/review, assemblies, sharing, CI).
  - **Quickstart** with a CI-safe preview snippet:
    ```python
    if __name__ == "__main__":
        try:
            from ocp_vscode import show
            show(result)
        except ImportError:
            pass  # dev-only dependency
    ```
  - **Caveats:** interpreter coupling, VSCodium needs `.vsix` side-load (not on Open VSX), WebGL/remote-SSH lag, not a mesh editor, does not replace committed renders.
- **`README.md`** — adds a "Tooling notes" section linking the assessment.

Docs-only; no code or build changes.

### PR #74 [OPEN]: Add chronological Record of Designs (DESIGN-LOG.md)
Issue #73 asks for a single, scrollable record documenting every design — and every iteration of every design — created in this repository, in chronological order, each with render visuals and a short note on what changed and why.

## `DESIGN-LOG.md`
- **97 entries**, ordered oldest → newest (2026-04-23 → 2026-05-28), from the original hand-sketched scoop through the hinged multi-part mounting-plate assembly.
- **One entry per design version**, placed by commit date — iterations are *not* grouped by object (e.g. auger bracket v1→v4, mounting plate v1→v7, excavator concept v1→v6).
- Each entry carries a **Trigger** (the issue/comment/review that prompted it, with author) and a 1–2 sentence **Design** summary of what changed and why, drawn from the actual PR/issue/review text.
- **176 render views** (iso/front/top/side/cross-section/assembly/exploded), 1–3 per entry.

## Rendering approach
Most designs live on still-open PR branches. Rather than copy ~hundreds of MB of binaries, visuals are embedded via `raw.githubusercontent.com` URLs **pinned to each iteration's exact commit SHA**, so a thumbnail shows that *specific* version even when later iterations reused the same filename:

```
https://raw.githubusercontent.com/vertical-cloud-lab/powder-doser/<commit-sha>/cad/auger-bracket/views/iso.png
```

## `README.md`
- Adds a "Record of designs" section linking the log.

## Notes for reviewers
- Image links are pinned to commits on (mostly unmerged) source branches. They resolve today; if those branch commits are ever GC'd, the affected images would need re-pinning.
- Entry segmentation favors capturing distinct iterations; reviewers may want to merge/split a few borderline cases (pure-docs commits were intentionally excluded).

### PR #76 [OPEN]: Add literature search for generative electrical and PCB design
Extends the `paper/background/` Edison Scientific literature review from generative **CAD** (issue #28 / PR #29) to generative **electrical and PCB design**, the natural complement now that the repo's hardware includes microcontroller-driven KiCad control electronics (steppers, vibration motors, solenoids, servos, load-cell feedback; issues #25/#44/#60, PRs #45/#61).

Seven high-effort `LITERATURE_HIGH` queries were dispatched in parallel via `EdisonClient.run_tasks_until_done` (all returned `status=success`).

### Runner
- **`edison_run_electrical_pcb.py`** — self-contained, re-runnable (`EDISON_API_KEY` from env), prompts embedded verbatim, writes `<key>.{task.json,answer.md,references.md}`. Mirrors the existing `edison_run.py` convention.

### Notes (`07`–`13`, verbatim with inline `(authorYYYY pages X-Y)` keys + numbered references)
- **07** generative EDA/PCB tools landscape — the dedicated *state-of-the-art tools* query (KiCad, Altium, Cadence Allegro/OrCAD X, Siemens, Zuken, Fusion/EAGLE; Flux.ai, JITX, Quilter, DeepPCB, Celus; atopile, tscircuit, SKiDL, gEDA, Horizon EDA)
- **08** generative schematic / circuit-topology synthesis
- **09** ML/RL placement & routing (incl. Google Nature 2021 + critiques)
- **10** LLM HDL / hardware code generation (VerilogEval, RTLLM, ChipGPT, AnalogCoder, LaMAGIC…)
- **11** code-based / design-as-code EDA for CI workflows
- **12** datasets & benchmarks for generative EDA
- **13** generative/automated EDA for open-hardware lab automation

### Provenance & docs
- Raw artifacts (~13 MB `TaskResponse` JSON + rendered answers + references) under `edison_artifacts/`; no API keys present.
- `README.md` for the background folder (pillar/scope table, drafting workflow, reproduction steps) and `edison_artifacts/README.md` (artifact layout).

Notes are kept verbatim so citation provenance is preserved when passages are pulled into `paper/main.tex` / `paper/rsc.bib` during the proposal writing pass. Numbering continues from the CAD pillar (`01`–`06`, PR #29), which is not on this branch's base.

### PR #78 [OPEN]: Add Utah AI Convergence poster abstract
Responding to #77 and creating deliverables for the conference

### PR #79 [CLOSED]: chore: add Copilot responder Action (automations/copilot-respond)
Relates to https://github.com/vertical-cloud-lab/powder-doser/pull/76

This PR adds a minimal GitHub Action and script that responds to issue/PR comments containing "@copilot".

Behavior:

When a comment includes "@copilot", the action calls an LLM with the comment text and posts the generated reply as a new issue/PR comment.
Each reply is prefixed with "Copilot Response:" for provenance.
Secrets required: OPENAI_API_KEY (required), BOT_TOKEN (optional).
Notes: replies are posted by github-actions[bot] unless BOT_TOKEN is configured.
