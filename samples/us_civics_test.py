from genanki import Note, Model, Deck, Package

# Create a model for the flashcards
civics_model = Model(
    1607392319,  # Random model ID
    "US Civics Test Model",
    fields=[
        {"name": "Question"},
        {"name": "Answer"},
    ],
    templates=[
        {
            "name": "Card 1",
            "qfmt": """
                <div style="font-family: Arial; font-size: 20px; text-align: center; color: #2c3e50;">
                    {{Question}}
                </div>
            """,
            "afmt": """
                <div style="font-family: Arial; font-size: 20px; text-align: center; color: #2c3e50;">
                    {{Question}}
                </div>
                <hr id="answer" style="border: 1px solid #bdc3c7; margin: 20px 0;">
                <div style="font-family: Arial; font-size: 18px; color: #27ae60; padding: 10px; background-color: #f8f9fa; border-radius: 5px;">
                    {{Answer}}
                </div>
            """,
        },
    ],
)

# Create a deck
deck_name = "US Civics Test"
package_name = deck_name.lower().replace(" ", "_")
civics_deck = Deck(2059400110, deck_name)

# All 100 official USCIS civics questions and answers
questions_answers = [
    ("What is the supreme law of the land?", "the Constitution"),
    ("What does the Constitution do?", "sets up the government<br/>defines the government<br/>protects basic rights of Americans"),
    ("The idea of self-government is in the first three words of the Constitution. What are these words?", "We the People"),
    ("What is an amendment?", "a change (to the Constitution)<br/>an addition (to the Constitution)"),
    ("What do we call the first ten amendments to the Constitution?", "the Bill of Rights"),
    ("What is one right or freedom from the First Amendment?", "speech<br/>religion<br/>assembly<br/>press<br/>petition the government"),
    ("How many amendments does the Constitution have?", "twenty-seven (27)"),
    ("What did the Declaration of Independence do?", "announced our independence (from Great Britain)<br/>declared our independence (from Great Britain)<br/>said that the United States is free (from Great Britain)"),
    ("What are two rights in the Declaration of Independence?", "life<br/>liberty<br/>pursuit of happiness"),
    ("What is freedom of religion?", "You can practice any religion, or not practice a religion."),
    ("What is the economic system in the United States?", "capitalist economy<br/>market economy"),
    ("What is the 'rule of law'?", "Everyone must follow the law.<br/>Leaders must obey the law.<br/>Government must obey the law.<br/>No one is above the law."),
    ("Name one branch or part of the government.", "Congress<br/>legislative<br/>President<br/>executive<br/>the courts<br/>judicial"),
    ("What stops one branch of government from becoming too powerful?", "checks and balances<br/>separation of powers"),
    ("Who is in charge of the executive branch?", "the President"),
    ("Who makes federal laws?", "Congress<br/>Senate and House (of Representatives)<br/>(U.S. or national) legislature"),
    ("What are the two parts of the U.S. Congress?", "the Senate and House (of Representatives)"),
    ("How many U.S. Senators are there?", "one hundred (100)"),
    ("We elect a U.S. Senator for how many years?", "six (6)"),
    ("Who is one of your state's U.S. Senators now?", "Answers will vary."),
    ("The House of Representatives has how many voting members?", "four hundred thirty-five (435)"),
    ("We elect a U.S. Representative for how many years?", "two (2)"),
    ("Name your U.S. Representative.", "Answers will vary."),
    ("Who does a U.S. Senator represent?", "all people of the state"),
    ("Why do some states have more Representatives than other states?", "(because of) the state's population<br/>(because) they have more people<br/>(because) some states have more people"),
    ("We elect a President for how many years?", "four (4)"),
    ("In what month do we vote for President?", "November"),
    ("What is the name of the President of the United States now?", "Visit uscis.gov/citizenship/testupdates for the name of the President of the United States."),
    ("What is the name of the Vice President of the United States now?", "Visit uscis.gov/citizenship/testupdates for the name of the Vice President of the United States."),
    ("If the President can no longer serve, who becomes President?", "the Vice President"),
    ("If both the President and the Vice President can no longer serve, who becomes President?", "the Speaker of the House"),
    ("Who is the Commander in Chief of the military?", "the President"),
    ("Who signs bills to become laws?", "the President"),
    ("Who vetoes bills?", "the President"),
    ("What does the President's Cabinet do?", "advises the President"),
    ("What are two Cabinet-level positions?", "Secretary of Agriculture<br/>Secretary of Commerce<br/>Secretary of Defense<br/>Secretary of Education<br/>Secretary of Energy<br/>Secretary of Health and Human Services<br/>Secretary of Homeland Security<br/>Secretary of Housing and Urban Development<br/>Secretary of the Interior<br/>Secretary of Labor<br/>Secretary of State<br/>Secretary of Transportation<br/>Secretary of the Treasury<br/>Secretary of Veterans Affairs<br/>Attorney General<br/>Vice President"),
    ("What does the judicial branch do?", "reviews laws<br/>explains laws<br/>resolves disputes (disagreements)<br/>decides if a law goes against the Constitution"),
    ("What is the highest court in the United States?", "the Supreme Court"),
    ("How many justices are on the Supreme Court?", "Visit uscis.gov/citizenship/testupdates for the number of justices on the Supreme Court."),
    ("Who is the Chief Justice of the United States now?", "Visit uscis.gov/citizenship/testupdates for the name of the Chief Justice of the United States."),
    ("Under our Constitution, some powers belong to the federal government. What is one power of the federal government?", "to print money<br/>to declare war<br/>to create an army<br/>to make treaties"),
    ("Under our Constitution, some powers belong to the states. What is one power of the states?", "provide schooling and education<br/>provide protection (police)<br/>provide safety (fire departments)<br/>give a driver's license<br/>approve zoning and land use"),
    ("Who is the Governor of your state now?", "Answers will vary."),
    ("What is the capital of your state?", "Answers will vary."),
    ("What are the two major political parties in the United States?", "Democratic and Republican"),
    ("What is the political party of the President now?", "Visit uscis.gov/citizenship/testupdates for the political party of the President."),
    ("What is the name of the Speaker of the House of Representatives now?", "Visit uscis.gov/citizenship/testupdates for the name of the Speaker of the House of Representatives."),
    ("There are four amendments to the Constitution about who can vote. Describe one of them.", "Citizens eighteen (18) and older (can vote).<br/>You don't have to pay (a poll tax) to vote.<br/>Any citizen can vote. (Women and men can vote.)<br/>A male citizen of any race (can vote)."),
    ("What is one responsibility that is only for United States citizens?", "serve on a jury<br/>vote in a federal election"),
    ("Name one right only for United States citizens.", "vote in a federal election<br/>run for federal office"),
    ("What are two rights of everyone living in the United States?", "freedom of expression<br/>freedom of speech<br/>freedom of assembly<br/>freedom to petition the government<br/>freedom of religion<br/>the right to bear arms"),
    ("What do we show loyalty to when we say the Pledge of Allegiance?", "the United States<br/>the flag"),
    ("What is one promise you make when you become a United States citizen?", "give up loyalty to other countries<br/>defend the Constitution and laws of the United States<br/>obey the laws of the United States<br/>serve in the U.S. military (if needed)<br/>serve (do important work for) the nation (if needed)<br/>be loyal to the United States"),
    ("How old do citizens have to be to vote for President?", "eighteen (18) and older"),
    ("What are two ways that Americans can participate in their democracy?", "vote<br/>join a political party<br/>help with a campaign<br/>join a civic group<br/>join a community group<br/>give an elected official your opinion on an issue<br/>call Senators and Representatives<br/>publicly support or oppose an issue or policy<br/>run for office<br/>write to a newspaper"),
    ("When is the last day you can send in federal income tax forms?", "April 15"),
    ("When must all men register for the Selective Service?", "at age eighteen (18)<br/>between eighteen (18) and twenty-six (26)"),
    ("What is one reason colonists came to America?", "freedom<br/>political liberty<br/>religious freedom<br/>economic opportunity<br/>practice their religion<br/>escape persecution"),
    ("Who lived in America before the Europeans arrived?", "American Indians<br/>Native Americans"),
    ("What group of people was taken to America and sold as slaves?", "Africans<br/>people from Africa"),
    ("Why did the colonists fight the British?", "because of high taxes (taxation without representation)<br/>because the British army stayed in their houses (boarding, quartering)<br/>because they didn't have self-government"),
    ("Who wrote the Declaration of Independence?", "(Thomas) Jefferson"),
    ("When was the Declaration of Independence adopted?", "July 4, 1776"),
    ("There were 13 original states. Name three.", "New Hampshire<br/>Massachusetts<br/>Rhode Island<br/>Connecticut<br/>New York<br/>New Jersey<br/>Pennsylvania<br/>Delaware<br/>Maryland<br/>Virginia<br/>North Carolina<br/>South Carolina<br/>Georgia"),
    ("What happened at the Constitutional Convention?", "The Constitution was written.<br/>The Founding Fathers wrote the Constitution."),
    ("When was the Constitution written?", "1787"),
    ("The Federalist Papers supported the passage of the U.S. Constitution. Name one of the writers.", "(James) Madison<br/>(Alexander) Hamilton<br/>(John) Jay<br/>Publius"),
    ("What is one thing Benjamin Franklin is famous for?", "U.S. diplomat<br/>oldest member of the Constitutional Convention<br/>first Postmaster General of the United States<br/>writer of 'Poor Richard's Almanac'<br/>started the first free libraries"),
    ("Who is the 'Father of Our Country'?", "(George) Washington"),
    ("Who was the first President?", "(George) Washington"),
    ("What territory did the United States buy from France in 1803?", "the Louisiana Territory<br/>Louisiana"),
    ("Name one war fought by the United States in the 1800s.", "War of 1812<br/>Mexican-American War<br/>Civil War<br/>Spanish-American War"),
    ("Name the U.S. war between the North and the South.", "the Civil War<br/>the War between the States"),
    ("Name one problem that led to the Civil War.", "slavery<br/>economic reasons<br/>states' rights"),
    ("What was one important thing that Abraham Lincoln did?", "freed the slaves (Emancipation Proclamation)<br/>saved (or preserved) the Union<br/>led the United States during the Civil War"),
    ("What did the Emancipation Proclamation do?", "freed the slaves<br/>freed slaves in the Confederacy<br/>freed slaves in the Confederate states<br/>freed slaves in most Southern states"),
    ("What did Susan B. Anthony do?", "fought for women's rights<br/>fought for civil rights"),
    ("Name one war fought by the United States in the 1900s.", "World War I<br/>World War II<br/>Korean War<br/>Vietnam War<br/>(Persian) Gulf War"),
    ("Who was President during World War I?", "(Woodrow) Wilson"),
    ("Who was President during the Great Depression and World War II?", "(Franklin) Roosevelt"),
    ("Who did the United States fight in World War II?", "Japan, Germany, and Italy"),
    ("Before he was President, Eisenhower was a general. What war was he in?", "World War II"),
    ("During the Cold War, what was the main concern of the United States?", "Communism"),
    ("What movement tried to end racial discrimination?", "civil rights (movement)"),
    ("What did Martin Luther King, Jr. do?", "fought for civil rights<br/>worked for equality for all Americans"),
    ("What major event happened on September 11, 2001, in the United States?", "Terrorists attacked the United States."),
    ("Name one American Indian tribe in the United States.", "Cherokee<br/>Navajo<br/>Sioux<br/>Chippewa<br/>Choctaw<br/>Pueblo<br/>Apache<br/>Iroquois<br/>Creek<br/>Blackfeet<br/>Seminole<br/>Cheyenne<br/>Arawak<br/>Shawnee<br/>Mohegan<br/>Huron<br/>Oneida<br/>Lakota<br/>Crow<br/>Teton<br/>Hopi<br/>Inuit"),
    ("Name one of the two longest rivers in the United States.", "Missouri (River)<br/>Mississippi (River)"),
    ("What ocean is on the West Coast of the United States?", "Pacific (Ocean)"),
    ("What ocean is on the East Coast of the United States?", "Atlantic (Ocean)"),
    ("Name one U.S. territory.", "Puerto Rico<br/>U.S. Virgin Islands<br/>American Samoa<br/>Northern Mariana Islands<br/>Guam"),
    ("Name one state that borders Canada.", "Maine<br/>New Hampshire<br/>Vermont<br/>New York<br/>Pennsylvania<br/>Ohio<br/>Michigan<br/>Minnesota<br/>North Dakota<br/>Montana<br/>Idaho<br/>Washington<br/>Alaska"),
    ("Name one state that borders Mexico.", "California<br/>Arizona<br/>New Mexico<br/>Texas"),
    ("What is the capital of the United States?", "Washington, D.C."),
    ("Where is the Statue of Liberty?", "New York (Harbor)<br/>Liberty Island<br/>Also acceptable are New Jersey, near New York City, and on the Hudson (River)."),
    ("Why does the flag have 13 stripes?", "because there were 13 original colonies<br/>because the stripes represent the original colonies"),
    ("Why does the flag have 50 stars?", "because there is one star for each state<br/>because each star represents a state<br/>because there are 50 states"),
    ("What is the name of the national anthem?", "The Star-Spangled Banner"),
    ("When do we celebrate Independence Day?", "July 4"),
    ("Name two national U.S. holidays.", "New Year's Day<br/>Martin Luther King, Jr. Day<br/>Presidents' Day<br/>Memorial Day<br/>Independence Day<br/>Labor Day<br/>Columbus Day<br/>Veterans Day<br/>Thanksgiving<br/>Christmas")
]

# Add notes to the deck
for question, answer in questions_answers:
    note = Note(model=civics_model, fields=[question, answer])
    civics_deck.add_note(note)

# Create the package
Package(civics_deck).write_to_file(f"{package_name}.apkg")

if __name__ == "__main__":
    print(f"Created {deck_name} flashcards package: {package_name}.apkg")
