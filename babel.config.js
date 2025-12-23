module.exports = function (api) {
  api.cache(true);
  const isWeb = process.env.EXPO_WEB === 'true' || process.env.BABEL_ENV === 'web';
  return {
    presets: ['babel-preset-expo'],
    plugins: isWeb ? [] : ['react-native-reanimated/plugin'],
  };
};