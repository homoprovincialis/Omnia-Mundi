export function allocate(cents, weights) {
  if (!Number.isSafeInteger(cents) || cents < 0 || !weights.length || weights.some(w => !Number.isSafeInteger(w) || w <= 0)) throw new Error('Invalid allocation');
  const total = weights.reduce((a,b)=>a+b,0);
  if (!Number.isSafeInteger(cents * total)) throw new Error('Amount too large');
  const parts = weights.map(w=>Math.floor(cents*w/total));
  const order = weights.map((w,i)=>({i,r:cents*w%total})).sort((a,b)=>b.r-a.r||a.i-b.i);
  for(let n=cents-parts.reduce((a,b)=>a+b,0),i=0;i<n;i++) parts[order[i].i]++;
  return parts;
}
export const sourceTypes = Object.freeze(['Procurer', 'Manufacturer', 'Seller']);
export function tradeProfit(netCents, sourceType) {
  if (!sourceTypes.includes(sourceType)) throw new Error('A single valid sourceType is required');
  // Allocate the five primary shares first; internal amounts must sum to Moderator's share.
  const [source, receiver, moderator, omniaMundi, protectionFund] = allocate(netCents, [20,20,20,20,20]);
  return {sourceType, source, receiver, moderator, omniaMundi, protectionFund,
    moderatorInternal: allocate(moderator, [5,5,10])};
}
export const businessProfit = cents => allocate(cents,[35,35,30]);
export function freeReward(cents, participantCount) {
  if (!Number.isInteger(participantCount)||participantCount<1||participantCount>100) throw new Error('Actual participants required');
  return allocate(cents,Array(participantCount+1).fill(1));
}
