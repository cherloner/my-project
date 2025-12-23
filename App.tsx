import 'react-native-gesture-handler';
import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Image,
  Alert,
  SafeAreaView,
} from 'react-native';
import { NavigationContainer, DefaultTheme as NavDefaultTheme } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { MaterialIcons } from '@expo/vector-icons';
import { Provider as PaperProvider, Button, Searchbar, Chip, ProgressBar, Switch, TextInput } from 'react-native-paper';
import { Video, AVPlaybackStatus, AVPlaybackStatusSuccess } from 'expo-av';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as DocumentPicker from 'expo-document-picker';

// -------------------- Mock Data --------------------
export type VideoItem = {
  id: string;
  title: string;
  author: string;
  durationSec: number;
  cover: string;
  url: string;
  tags: string[];
  language: string;
};

const mockVideos: VideoItem[] = [
  {
    id: 'v1',
    title: '算法基础：时间复杂度入门',
    author: 'Alice',
    durationSec: 120,
    cover: 'https://images.unsplash.com/photo-1518779578993-ec3579fee39f?q=80&w=800&auto=format&fit=crop',
    url: 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8',
    tags: ['算法', '数据结构'],
    language: 'zh',
  },
  {
    id: 'v2',
    title: '英语口语：日常对话技巧',
    author: 'Bob',
    durationSec: 160,
    cover: 'https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?q=80&w=800&auto=format&fit=crop',
    url: 'https://www.w3schools.com/html/mov_bbb.mp4',
    tags: ['英语', '口语'],
    language: 'en',
  },
  {
    id: 'v3',
    title: 'React Hooks 快速上手',
    author: 'Carol',
    durationSec: 175,
    cover: 'https://images.unsplash.com/photo-1556157382-97eda2d62296?q=80&w=800&auto=format&fit=crop',
    url: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
    tags: ['前端', 'React'],
    language: 'zh',
  },
];

// -------------------- Navigation Types --------------------
const HomeFeedStack = createNativeStackNavigator();
const SearchStack = createNativeStackNavigator();
const UploadStack = createNativeStackNavigator();
const MeStack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

// -------------------- Screens: Home Feed --------------------
function FeedScreen({ navigation }: any) {
  return (
    <SafeAreaView style={{ flex: 1 }}>
      <FlatList
        data={mockVideos}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ padding: 12 }}
        renderItem={({ item }) => (
          <TouchableOpacity
            onPress={() => navigation.navigate('VideoDetail', { item })}
            onLongPress={() => Alert.alert('快捷操作', '是否收藏/稍后看？', [
              { text: '收藏', onPress: () => Alert.alert('已收藏') },
              { text: '稍后看', onPress: () => Alert.alert('已加入稍后看') },
              { text: '取消', style: 'cancel' },
            ])}
            style={styles.card}
          >
            <Image source={{ uri: item.cover }} style={styles.cover} />
            <View style={{ padding: 12 }}>
              <Text style={styles.title}>{item.title}</Text>
              <Text style={styles.meta}>{item.author} · {Math.round(item.durationSec / 60)} 分钟</Text>
              <View style={{ flexDirection: 'row', marginTop: 6 }}>
                {item.tags.slice(0, 3).map((t) => (
                  <Chip key={t} style={{ marginRight: 6 }} compact>{t}</Chip>
                ))}
              </View>
            </View>
          </TouchableOpacity>
        )}
      />
    </SafeAreaView>
  );
}

function VideoDetailScreen({ route }: any) {
  const { item }: { item: VideoItem } = route.params;
  const videoRef = useRef<Video>(null);
  const [status, setStatus] = useState<AVPlaybackStatus | null>(null);
  const [rate, setRate] = useState<number>(1);
  const [lastHeartbeat, setLastHeartbeat] = useState<number>(0);

  // Load last position
  useEffect(() => {
    (async () => {
      const saved = await AsyncStorage.getItem(`progress:${item.id}`);
      const parsed = saved ? JSON.parse(saved) : null;
      if (parsed?.position && videoRef.current) {
        try {
          await videoRef.current.setStatusAsync({ positionMillis: parsed.position });
        } catch {}
      }
    })();
  }, [item.id]);

  const onStatusUpdate = async (s: AVPlaybackStatus) => {
    setStatus(s);
    if (!('positionMillis' in s)) return;
    const now = Date.now();
    const intervalMs = 10000; // 10s 心跳
    if (now - lastHeartbeat >= intervalMs || (s as AVPlaybackStatusSuccess).didJustFinish || !s.isPlaying) {
      setLastHeartbeat(now);
      const payload = {
        position: (s as AVPlaybackStatusSuccess).positionMillis,
        duration: (s as AVPlaybackStatusSuccess).durationMillis ?? 0,
        playing: (s as AVPlaybackStatusSuccess).isPlaying ?? false,
      };
      await AsyncStorage.setItem(`progress:${item.id}`, JSON.stringify(payload));
    }

    if ((s as AVPlaybackStatusSuccess).didJustFinish) {
      Alert.alert('学习完成', '标记为：', [
        {
          text: '已学', onPress: async () => {
            await AsyncStorage.setItem(`learning_state:${item.id}`, 'done');
          }
        },
        {
          text: '需复习', onPress: async () => {
            await AsyncStorage.setItem(`learning_state:${item.id}`, 'review');
          }
        },
      ]);
    }
  };

  const skipBy = async (ms: number) => {
    if (!status || !('positionMillis' in status)) return;
    const next = Math.max(0, ((status as AVPlaybackStatusSuccess).positionMillis ?? 0) + ms);
    try {
      await videoRef.current?.setStatusAsync({ positionMillis: next });
    } catch {}
  };

  const changeRate = async (r: number) => {
    setRate(r);
    try {
      await videoRef.current?.setRateAsync(r, true);
    } catch {}
  };

  return (
    <View style={{ flex: 1 }}>
      <Video
        ref={videoRef}
        style={{ width: '100%', height: 240, backgroundColor: '#000' }}
        source={{ uri: item.url }}
        resizeMode="contain"
        useNativeControls
        onPlaybackStatusUpdate={onStatusUpdate}
      />
      <View style={{ padding: 12 }}>
        <Text style={styles.title}>{item.title}</Text>
        <Text style={styles.meta}>{item.author}</Text>
        <View style={styles.controlsRow}>
          <Button mode="outlined" onPress={() => skipBy(-15000)} icon={() => <MaterialIcons name="replay" size={20} />}>后退15秒</Button>
          <Button mode="outlined" onPress={() => skipBy(15000)} icon={() => <MaterialIcons name="forward" size={20} />}>快进15秒</Button>
        </View>
        <View style={styles.controlsRow}>
          {[0.75, 1, 1.25, 1.5, 2].map((r) => (
            <Button key={r} mode={r === rate ? 'contained' : 'outlined'} style={{ marginRight: 8 }} onPress={() => changeRate(r)}>
              {r}x
            </Button>
          ))}
        </View>
      </View>
    </View>
  );
}

function CommentsScreen() {
  return (
    <View style={styles.center}> 
      <Text>评论（楼中楼）——占位</Text>
    </View>
  );
}

function AuthorProfileScreen() {
  return (
    <View style={styles.center}> 
      <Text>作者主页——占位</Text>
    </View>
  );
}

function HomeFeedStackNavigator() {
  return (
    <HomeFeedStack.Navigator>
      <HomeFeedStack.Screen name="Feed" component={FeedScreen} options={{ title: '首页' }} />
      <HomeFeedStack.Screen name="VideoDetail" component={VideoDetailScreen} options={{ title: '播放' }} />
      <HomeFeedStack.Screen name="Comments" component={CommentsScreen} options={{ title: '评论' }} />
      <HomeFeedStack.Screen name="AuthorProfile" component={AuthorProfileScreen} options={{ title: '作者' }} />
    </HomeFeedStack.Navigator>
  );
}

// -------------------- Screens: Search --------------------
function SearchScreen({ navigation }: any) {
  const [query, setQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const tags = ['算法', '英语', 'React', '数据结构', '口语'];

  const toggleTag = (t: string) => {
    setSelectedTags((prev) => (prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]));
  };

  return (
    <View style={{ flex: 1, padding: 12 }}>
      <Searchbar placeholder="搜索关键词" value={query} onChangeText={setQuery} onSubmitEditing={() => navigation.navigate('Results', { query, tags: selectedTags })} />
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginTop: 8 }}>
        {tags.map((t) => (
          <Chip key={t} selected={selectedTags.includes(t)} onPress={() => toggleTag(t)} style={{ marginRight: 6, marginBottom: 6 }}>{t}</Chip>
        ))}
      </View>
      <Button mode="contained" onPress={() => navigation.navigate('Results', { query, tags: selectedTags })}>查看结果</Button>
    </View>
  );
}

function ResultsScreen({ route }: any) {
  const { query, tags = [] } = route.params || {};
  const results = mockVideos.filter((v) => {
    const q = query?.trim().toLowerCase();
    const hitQuery = !q || v.title.toLowerCase().includes(q) || v.author.toLowerCase().includes(q);
    const hitTags = tags.length === 0 || tags.every((t: string) => v.tags.includes(t));
    return hitQuery && hitTags;
  });
  return (
    <FlatList
      data={results}
      keyExtractor={(i) => i.id}
      contentContainerStyle={{ padding: 12 }}
      ListEmptyComponent={<Text style={{ textAlign: 'center', marginTop: 24 }}>暂无匹配结果</Text>}
      renderItem={({ item }) => (
        <View style={styles.card}>
          <Image source={{ uri: item.cover }} style={styles.cover} />
          <View style={{ padding: 12 }}>
            <Text style={styles.title}>{item.title}</Text>
            <Text style={styles.meta}>{item.author}</Text>
          </View>
        </View>
      )}
    />
  );
}

function SearchStackNavigator() {
  return (
    <SearchStack.Navigator>
      <SearchStack.Screen name="Search" component={SearchScreen} options={{ title: '搜索' }} />
      <SearchStack.Screen name="Results" component={ResultsScreen} options={{ title: '结果' }} />
    </SearchStack.Navigator>
  );
}

// -------------------- Screens: Upload --------------------
function PickMediaScreen({ navigation }: any) {
  const [pickedName, setPickedName] = useState<string>('');
  const [uri, setUri] = useState<string>('');

  const pick = async () => {
    const res = await DocumentPicker.getDocumentAsync({ type: 'video/*', copyToCacheDirectory: true });
    if ((res as any).type === 'cancel') return;
    const asset = res as any;
    setPickedName(asset.name || '所选视频');
    setUri(asset.uri);
    navigation.navigate('EditTrim', { uri: asset.uri, name: asset.name });
  };

  return (
    <View style={styles.center}> 
      <Button mode="contained" onPress={pick} icon={() => <MaterialIcons name="video-library" size={18} />}>选择视频（≤180s）</Button>
      {pickedName ? <Text style={{ marginTop: 12 }}>{pickedName}</Text> : null}
    </View>
  );
}

function EditTrimScreen({ route, navigation }: any) {
  const { uri, name } = route.params || {};
  const videoRef = useRef<Video>(null);
  const [durationMs, setDurationMs] = useState<number>(0);

  const onStatusUpdate = (s: AVPlaybackStatus) => {
    if ('durationMillis' in s && s.durationMillis && s.durationMillis !== durationMs) {
      setDurationMs(s.durationMillis);
      if (s.durationMillis > 180000) {
        Alert.alert('时长超限', '仅允许 ≤180 秒的视频', [
          { text: '确定', onPress: () => navigation.goBack() },
        ]);
      }
    }
  };

  return (
    <View style={{ flex: 1 }}>
      {!!uri && (
        <Video
          ref={videoRef}
          source={{ uri }}
          style={{ width: '100%', height: 240, backgroundColor: '#000' }}
          resizeMode="contain"
          useNativeControls
          onPlaybackStatusUpdate={onStatusUpdate}
        />
      )}
      <View style={{ padding: 12 }}>
        <Text style={styles.title}>基础裁剪（占位）</Text>
        <Button mode="contained" onPress={() => navigation.navigate('MetaForm', { uri, name })}>下一步</Button>
      </View>
    </View>
  );
}

function MetaFormScreen({ route, navigation }: any) {
  const { uri, name } = route.params || {};
  const [title, setTitle] = useState('');
  const [desc, setDesc] = useState('');
  const [isPublic, setIsPublic] = useState(true);
  const [tags, setTags] = useState<string[]>([]);
  const availableTags = ['算法', '英语', 'React', '数据结构', '口语'];

  const toggleTag = (t: string) => setTags((prev) => (prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]));

  return (
    <View style={{ flex: 1, padding: 12 }}>
      <TextInput label="标题（2-40字）" value={title} onChangeText={setTitle} style={{ marginBottom: 8 }} />
      <TextInput label="描述（≤500字）" value={desc} onChangeText={setDesc} multiline style={{ marginBottom: 8 }} />
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginVertical: 8 }}>
        {availableTags.map((t) => (
          <Chip key={t} selected={tags.includes(t)} onPress={() => toggleTag(t)} style={{ marginRight: 6, marginBottom: 6 }}>{t}</Chip>
        ))}
      </View>
      <View style={{ flexDirection: 'row', alignItems: 'center', marginVertical: 8 }}>
        <Text style={{ marginRight: 8 }}>公开可见</Text>
        <Switch value={isPublic} onValueChange={setIsPublic} />
      </View>
      <Button mode="contained" onPress={() => navigation.navigate('Uploading', { uri, meta: { title, desc, isPublic, tags } })}>提交上传</Button>
    </View>
  );
}

function UploadingScreen({ route, navigation }: any) {
  const [progress, setProgress] = useState(0);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      setProgress((p) => {
        if (paused) return p;
        const next = Math.min(1, p + 0.05);
        if (next >= 1) {
          clearInterval(timer);
          setTimeout(() => navigation.replace('ReviewStatus', { status: '待审核' }), 500);
        }
        return next;
      });
    }, 300);
    return () => clearInterval(timer);
  }, [paused]);

  return (
    <View style={{ flex: 1, padding: 12 }}>
      <Text>分片上传中（模拟）</Text>
      <ProgressBar progress={progress} style={{ marginVertical: 12 }} />
      <View style={styles.controlsRow}>
        <Button mode="outlined" onPress={() => setPaused((v) => !v)}>{paused ? '继续' : '暂停'}</Button>
        <Button mode="outlined" onPress={() => setProgress(0)}>重传</Button>
      </View>
    </View>
  );
}

function ReviewStatusScreen({ route }: any) {
  const { status } = route.params || { status: '待审核' };
  return (
    <View style={styles.center}> 
      <Text>审核状态：{status}</Text>
      <Text style={{ marginTop: 8 }}>如被驳回会显示原因（占位）。</Text>
    </View>
  );
}

function UploadStackNavigator() {
  return (
    <UploadStack.Navigator>
      <UploadStack.Screen name="PickMedia" component={PickMediaScreen} options={{ title: '选择视频' }} />
      <UploadStack.Screen name="EditTrim" component={EditTrimScreen} options={{ title: '编辑/裁剪' }} />
      <UploadStack.Screen name="MetaForm" component={MetaFormScreen} options={{ title: '填写信息' }} />
      <UploadStack.Screen name="Uploading" component={UploadingScreen} options={{ title: '上传中' }} />
      <UploadStack.Screen name="ReviewStatus" component={ReviewStatusScreen} options={{ title: '审核状态' }} />
    </UploadStack.Navigator>
  );
}

// -------------------- Screens: Inbox --------------------
function InboxScreen() {
  return (
    <View style={{ flex: 1, padding: 12 }}>
      <Text>消息与通知（占位）：评论回复、系统公告、审核结果</Text>
    </View>
  );
}

// -------------------- Screens: Me --------------------
function MeScreen({ navigation }: any) {
  return (
    <View style={{ flex: 1, padding: 12 }}>
      <Text style={styles.title}>我的</Text>
      <Text>累计学习时长、完成视频数（占位）</Text>
      <View style={{ marginTop: 12 }}>
        <Button mode="outlined" onPress={() => navigation.navigate('Settings')}>设置</Button>
        <Button mode="outlined" onPress={() => navigation.navigate('LearningRecords')}>学习记录</Button>
        <Button mode="outlined" onPress={() => navigation.navigate('Favorites')}>收藏夹</Button>
      </View>
    </View>
  );
}

function SettingsScreen() {
  return (
    <View style={styles.center}><Text>设置与偏好（占位）</Text></View>
  );
}
function LearningRecordsScreen() {
  return (
    <View style={styles.center}><Text>学习记录（占位）</Text></View>
  );
}
function FavoritesScreen() {
  return (
    <View style={styles.center}><Text>收藏夹（占位）</Text></View>
  );
}
function DownloadsScreen() {
  return (
    <View style={styles.center}><Text>离线下载（P1 占位）</Text></View>
  );
}

function MeStackNavigator() {
  return (
    <MeStack.Navigator>
      <MeStack.Screen name="Me" component={MeScreen} options={{ title: '我的' }} />
      <MeStack.Screen name="Settings" component={SettingsScreen} options={{ title: '设置' }} />
      <MeStack.Screen name="LearningRecords" component={LearningRecordsScreen} options={{ title: '学习记录' }} />
      <MeStack.Screen name="Favorites" component={FavoritesScreen} options={{ title: '收藏夹' }} />
      <MeStack.Screen name="Downloads" component={DownloadsScreen} options={{ title: '下载(P1)' }} />
    </MeStack.Navigator>
  );
}

// -------------------- Tabs --------------------
function MainTabs() {
  return (
    <Tab.Navigator screenOptions={{ headerShown: false }}>
      <Tab.Screen
        name="HomeFeed"
        component={HomeFeedStackNavigator}
        options={{
          tabBarLabel: '首页',
          tabBarIcon: ({ color, size }) => <MaterialIcons name="home" color={color} size={size} />,
        }}
      />
      <Tab.Screen
        name="Discover"
        component={SearchStackNavigator}
        options={{
          tabBarLabel: '搜索',
          tabBarIcon: ({ color, size }) => <MaterialIcons name="search" color={color} size={size} />,
        }}
      />
      <Tab.Screen
        name="Upload"
        component={UploadStackNavigator}
        options={{
          tabBarLabel: '上传',
          tabBarIcon: ({ color, size }) => <MaterialIcons name="cloud-upload" color={color} size={size} />,
        }}
      />
      <Tab.Screen
        name="Inbox"
        component={InboxScreen}
        options={{
          tabBarLabel: '消息',
          tabBarIcon: ({ color, size }) => <MaterialIcons name="notifications" color={color} size={size} />,
        }}
      />
      <Tab.Screen
        name="MeTab"
        component={MeStackNavigator}
        options={{
          tabBarLabel: '我的',
          tabBarIcon: ({ color, size }) => <MaterialIcons name="person" color={color} size={size} />,
        }}
      />
    </Tab.Navigator>
  );
}

// -------------------- App --------------------
export default function App() {
  const theme = useMemo(() => ({
    ...NavDefaultTheme,
    colors: {
      ...NavDefaultTheme.colors,
      primary: '#3D5AFE',
      card: '#fff',
      text: '#111',
    },
  }), []);

  return (
    <PaperProvider>
      <NavigationContainer theme={theme}>
        <MainTabs />
      </NavigationContainer>
    </PaperProvider>
  );
}

// -------------------- Styles --------------------
const styles = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 12 },
  controlsRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginVertical: 8 },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 12,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: '#ddd',
  },
  cover: { width: '100%', height: 160 },
  title: { fontSize: 18, fontWeight: '600' },
  meta: { fontSize: 12, color: '#666', marginTop: 4 },
});
