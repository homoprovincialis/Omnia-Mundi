import {test} from 'node:test';
import assert from 'node:assert/strict';
import {tradeProfit} from '../src/finance.js';
const primary = r => [r.source,r.receiver,r.moderator,r.omniaMundi,r.protectionFund];
for (const sourceType of ['Procurer','Manufacturer','Seller']) {
  test(`${sourceType} is the only goods source and all five recipients receive 20%`,()=>{
    const r=tradeProfit(10000,sourceType);
    assert.equal(r.sourceType,sourceType);
    assert.deepEqual(primary(r),[2000,2000,2000,2000,2000]);
    assert.deepEqual(r.moderatorInternal,[500,500,1000]);
    for(const key of ['procurer','manufacturer','seller'])assert.equal(key in r,false);
  });
  test(`${sourceType}: cents conserved, including zero, small values and maximum API amount`,()=>{
    for(const cents of [...Array(10000).keys(),100000000]) {
      const r=tradeProfit(cents,sourceType);
      assert.equal(primary(r).reduce((a,b)=>a+b,0),cents);
      assert.equal(r.moderatorInternal.reduce((a,b)=>a+b,0),r.moderator);
      for(const value of [...primary(r),...r.moderatorInternal])assert.ok(Number.isSafeInteger(value)&&value>=0);
      for(const value of primary(r))assert.ok(Math.abs(value-cents/5)<1);
    }
  });
}
test('rounding uses deterministic largest remainders without double counting Moderator',()=>{
 assert.deepEqual(primary(tradeProfit(3,'Seller')),[1,1,1,0,0]);
 assert.deepEqual(tradeProfit(3,'Seller').moderatorInternal,[0,0,1]);
 assert.deepEqual(primary(tradeProfit(10003,'Seller')),[2001,2001,2001,2000,2000]);
 assert.deepEqual(tradeProfit(10003,'Seller').moderatorInternal,[500,500,1001]);
});
test('ambiguous, missing or invalid sources and invalid monetary amounts fail',()=>{
 for(const source of [undefined,null,'','Customer','Moderator',['Procurer','Seller'],{},'seller'])assert.throws(()=>tradeProfit(100,source));
 for(const cents of [-1,1.5,NaN,Infinity,Number.MAX_SAFE_INTEGER,'100'])assert.throws(()=>tradeProfit(cents,'Seller'));
});
