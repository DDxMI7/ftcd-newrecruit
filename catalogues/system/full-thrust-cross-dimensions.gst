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
    <costType id="cost-pts-0001" name="pts" defaultCostLimit="-1.0" hidden="false"/>
    <costType id="cost-mass-0001" name="Mass" defaultCostLimit="-1.0" hidden="false"/>
  </costTypes>

  <profileTypes>
    <profileType id="pt-shipstats-0001" name="Ship Stats">
      <characteristicTypes>
        <characteristicType id="ct-thrust-0001" name="Thrust Rating"/>
        <characteristicType id="ct-hull-0001" name="Hull Points"/>
        <characteristicType id="ct-firecons-0001" name="Firecons"/>
        <characteristicType id="ct-screen-0001" name="Screen Level"/>
        <characteristicType id="ct-armour-0001" name="Armour Grade"/>
      </characteristicTypes>
    </profileType>
    <profileType id="pt-weapon-0001" name="Weapon System">
      <characteristicTypes>
        <characteristicType id="ct-wclass-0001" name="Class"/>
        <characteristicType id="ct-range-0001" name="Max Range (MU)"/>
        <characteristicType id="ct-wdice-0001" name="Damage Dice"/>
        <characteristicType id="ct-arcs-0001" name="Fire Arcs"/>
      </characteristicTypes>
    </profileType>
    <profileType id="pt-rule-0001" name="Special Rule">
      <characteristicTypes>
        <characteristicType id="ct-ruledesc-0001" name="Description"/>
      </characteristicTypes>
    </profileType>
  </profileTypes>

  <categoryEntries>
    <categoryEntry id="cat-ship-0001"   name="Ship"           hidden="false"/>
    <categoryEntry id="cat-weapon-0001" name="Weapon System"  hidden="false"/>
    <categoryEntry id="cat-drive-0001"  name="Drive"          hidden="false"/>
    <categoryEntry id="cat-screen-0001" name="Screen"         hidden="false"/>
    <categoryEntry id="cat-pds-0001"    name="PDS"            hidden="false"/>
    <categoryEntry id="cat-special-0001" name="Special System" hidden="false"/>
  </categoryEntries>

  <forceEntries>
    <forceEntry id="fe-fleet-0001" name="Fleet" hidden="false">
      <rules>
        <rule id="rule-construction-0001" name="Ship Construction"
              publicationId="pub-ftcd-0001"
              description="Each ship has a mass (hull size). The total mass of all installed systems must not exceed the ship's available mass budget. Available mass = Hull Mass - Structural Mass - Drive Mass. Structural Mass = ceil(Hull Points / 2). Drive Mass = ceil(Thrust Rating / 2)."/>
        <rule id="rule-cpv-0001" name="Combat Point Value (CPV)"
              publicationId="pub-ftcd-0001"
              description="The pts cost shown is the Combat Point Value (CPV) of each system. Fleet sizes are agreed between players as a CPV limit."/>
      </rules>
      <categoryLinks>
        <categoryLink id="cl-ship-fleet-0001" name="Ships" hidden="false"
                      targetId="cat-ship-0001" primary="true">
          <constraints>
            <constraint id="con-minship-0001" type="min" value="1"
                        field="selections" scope="force" shared="true" includeChildSelections="false"/>
          </constraints>
        </categoryLink>
      </categoryLinks>
    </forceEntry>
  </forceEntries>

</gameSystem>
