<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<gameSystem id="ftcd-0001-gs01" name="Full Thrust Cross Dimensions"
            revision="1" battleScribeVersion="2.03"
            authorName="" authorContact="" authorUrl=""
            xmlns="http://www.battlescribe.net/schema/gameSystemSchema">
  <readme>Full Thrust Cross Dimensions — BattleScribe/New Recruit catalogue.
Based on the FTCD rulebook by Hugh Fisher and Jon Tuffley (Ground Zero Games, 2010).
Catalogue data by the FTCD community. Not officially endorsed by GZG.</readme>

  <publications>
    <publication id="pub-ftcd-0001" name="Full Thrust Cross Dimensions"
                 shortName="FTCD" publisher="Ground Zero Games"
                 publicationDate="2010" publisherUrl="http://groundzerogames.net"/>
  </publications>

  <costTypes>
    <costType id="7d62-4668-5257" name="pts"  defaultCostLimit="-1.0" hidden="false"/>
    <costType id="4771-3924-56de" name="Mass" defaultCostLimit="-1.0" hidden="false"/>
  </costTypes>

  <profileTypes>
    <profileType id="347a-bc89-60a9" name="Ship Stats">
      <characteristicTypes>
        <characteristicType id="1045-6c03-1199" name="Thrust"/>
        <characteristicType id="2ff8-07a0-ca6e" name="Hull Points"/>
        <characteristicType id="771f-37f8-a88b" name="Firecons"/>
        <characteristicType id="d6cb-8b81-48f6" name="Screens"/>
      </characteristicTypes>
    </profileType>
    <profileType id="e5fe-386e-cbe0" name="Weapon">
      <characteristicTypes>
        <characteristicType id="8e6f-96da-1dac" name="Class"/>
        <characteristicType id="51be-ce4a-2bbd" name="Max Range (MU)"/>
        <characteristicType id="d860-b2b9-437a" name="Damage Dice"/>
        <characteristicType id="8e45-571a-a876" name="Fire Arcs"/>
      </characteristicTypes>
    </profileType>
  </profileTypes>

  <categoryEntries>
    <categoryEntry id="876f-9a8d-ca03" name="Ship"            hidden="false"/>
    <categoryEntry id="163f-ce9f-f57f" name="Weapon"          hidden="false"/>
    <categoryEntry id="3fe9-8946-3e85" name="Drive"           hidden="false"/>
    <categoryEntry id="961b-8d52-88f1" name="Support"         hidden="false"/>
    <categoryEntry id="6273-93cd-59bf" name="Defence"         hidden="false"/>
  </categoryEntries>

  <forceEntries>
    <forceEntry id="fe-fleet-0001" name="Fleet" hidden="false">
      <rules>
        <rule id="rule-construction-0001" name="Ship Construction"
              publicationId="3900-a3b1-799d"
              description="Each ship has a mass (hull size). The total mass of all installed systems must not exceed the ship's available mass budget. Available mass = Hull Mass - Structural Mass - Drive Mass. Structural Mass = ceil(Hull Points / 2). Drive Mass = ceil(Thrust Rating / 2)."/>
        <rule id="rule-cpv-0001" name="Combat Point Value (CPV)"
              publicationId="3900-a3b1-799d"
              description="The pts cost shown is the Combat Point Value (CPV) of each system. Fleet sizes are agreed between players as a CPV limit."/>
      </rules>
      <categoryLinks>
        <categoryLink id="cl-ship-fleet-0001" name="Ships" hidden="false"
                      targetId="876f-9a8d-ca03" primary="true">
          <constraints>
            <constraint id="con-minship-0001" type="min" value="1"
                        field="selections" scope="force" shared="true" includeChildSelections="false"/>
          </constraints>
        </categoryLink>
      </categoryLinks>
    </forceEntry>
  </forceEntries>

</gameSystem>
