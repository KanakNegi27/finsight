
export const money = (value: number) =>
  `₹${value.toLocaleString("en-IN", {
    maximumFractionDigits: 2,
  })}`;

export const compactMoney = (value: number) => {
  const abs = Math.abs(value);

  if (abs >= 10000000) {
    return `₹${(value / 10000000).toFixed(2)}Cr`;
  }

  if (abs >= 100000) {
    return `₹${(value / 100000).toFixed(2)}L`;
  }

  if (abs >= 1000) {
    return `₹${(value / 1000).toFixed(1)}k`;
  }

  return `₹${value.toFixed(0)}`;
};
